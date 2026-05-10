from unstructured.partition.auto import partition
import os
import tempfile
from werkzeug.utils import secure_filename
from unstructured.documents.elements import Title, NarrativeText, ListItem, Table, Image as UnstructuredImage
import logging
from entities.models import Session, Document, db
from google import genai
from PIL import Image as PILImage, ImageOps
import pytesseract

UPLOAD_FOLDER= './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#Saving the file, creating a document and a session if needed
def save_file(file, etudiant, id_session=None):
    if id_session:
        session = Session.query.get(id_session)
        if not session or session.id_etudiant != etudiant.id:
            return {"message": "Invalid session or access denied"}, 403
    else:
        # Create a new session for the etudiant
        session = Session(id_etudiant=etudiant.id)
        db.session.add(session)
        db.session.commit()

    #save the file
    filename=secure_filename(file.filename)
    filepath=os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

     #create a new document for the session
    new_document = Document(id_session=session.id, title=file.filename, path=filepath)
    db.session.add(new_document)
    db.session.commit() 

    return{
        "message": "file saved successfully",
        "filepath": filepath,
        "id_document": new_document.id,
        "id_session": session.id

    }, 200

#Extract Elements with unstructured
def extract_elements(file_path: str, tmp_dir: str) -> tuple[list, str]:
    try:
        elements = partition(
                file_path,
                strategy="hi_res",
                extract_image_block_types=["Image"],
                extract_image_block_output_dir=tmp_dir
            )
        if sum(len(e.text or '') for e in elements) < 20:
            raise ValueError("Extracted text too short")
        return elements, "hi_res"

    except Exception as e:
        logging.warning(f"hi_res failed ({e}), falling back to fast")
        return partition(file_path, strategy="fast"), "fast"
    

#Describe document images
def describe_images(image_path, context, gemini_client):
    try:
        img = PILImage.open(image_path)

        # 1. FILTRAGE : ignorer les petites images (icônes/logos) ou les barres décoratives
        width, height = img.size
        if width < 150 or height < 150:
            return None
        ratio = width / height if height > 0 else 0
        if ratio > 5.0 or ratio < 0.2:
            return None
        
        # 2. NETTOYAGE : Conversion en nuances de gris et amélioration du contraste
        cleaned_img = img.convert('L')
        cleaned_img = ImageOps.autocontrast(cleaned_img)

        # 3. EXTRACTION DU TEXTE (OCR LOCAL)
        try:
            text_ocr = pytesseract.image_to_string(cleaned_img).strip()
        except Exception as e:
            logging.warning(f"Tesseract OCR failed: {e}")
            text_ocr = ""
        
        # 4. PRÉPARATION DU CONTEXTE ET ENVOI À GEMINI
        prompt = "Analyze and describe this image in detail. Extract any relevant text, diagrams, or facts."
        if context:
            prompt += f"\n\nTo help you understand, here is the text from the document immediately preceding this image:\n\"\"\"{context}\"\"\"\nPlease use this context to inform your explanation of the image."
        if text_ocr:
            prompt += f"\n\nHere is a raw OCR text pre-extracted from the image: '{text_ocr}'. Please interpret this text in the context of the whole image, correct any typos, and explain what it depicts."
                        
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[img, prompt],
        )
        desc = response.text
        if text_ocr:
            return f"[IMAGE TEXT]\n{text_ocr}  [GEMINI DESCRIPTION]\n{desc}"
        else:
            return f"[GEMINI DESCRIPTION]\n{desc}"
        
    except Exception as e:
        logging.error(f"Gemini image processing failed: {e}")
        return None
    

# Initialize Gemini client
def create_gemini_client() -> genai.Client | None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logging.warning("GEMINI_API_KEY not set — image description disabled")
        return None
    return genai.Client(api_key=api_key) 


#Build structured output
def build_structured_output(elements, gemini_client) -> list:
    structured_output = []
    current_section = {
        "title": "PREAMBLE",
        "types": set(),
        "content": [],   # minuscule, cohérent
        "pages": set(),
    }

    for el in elements:
        text = el.text.strip() if el.text else ""
        page = (
            el.metadata.page_number
            if hasattr(el, 'metadata') and hasattr(el.metadata, 'page_number')
            else None
        )

        if isinstance(el, UnstructuredImage):
            image_path = getattr(getattr(el, 'metadata', None), 'image_path', None)
            desc = None  # toujours initialisé
            if image_path and os.path.exists(image_path) and gemini_client:
                context = "\n".join(current_section["content"][-3:]).strip()
                desc = describe_images(image_path, context, gemini_client)
            if desc:
                current_section["content"].append(desc)
                current_section["types"].add("Image")
                if page:
                    current_section["pages"].add(page)
            continue

        if not text:
            continue

        if isinstance(el, Title):
            # heuristique : si le texte est trop long, ce n'est probablement pas un titre
            if len(text) > 100:
                current_section["content"].append(text)
                current_section["types"].add("NarrativeText")
                if page: current_section["pages"].add(page)
            else:
                if current_section["content"]:
                    structured_output.append({
                        **current_section,
                        "types": list(current_section["types"]),
                        "pages": sorted(current_section["pages"]),
                    })
                current_section = {
                    "title": text,
                    "types": set(),
                    "content": [],
                    "pages": {page} if page else set(),
                }
        elif isinstance(el, NarrativeText):
            current_section["content"].append(text)
            current_section["types"].add("NarrativeText")
            if page: current_section["pages"].add(page)
        elif isinstance(el, ListItem):
            current_section["content"].append(f"- {text}")
            current_section["types"].add("ListItem")
            if page: current_section["pages"].add(page)
        elif isinstance(el, Table):
            current_section["content"].append(f"[TABLE]\n{text}")
            current_section["types"].add("Table")
            if page: current_section["pages"].add(page)

    if current_section["content"]:
        structured_output.append({
            **current_section,
            "types": list(current_section["types"]),
            "pages": sorted(current_section["pages"]),
        })

    return structured_output


def extract_text(file_path: str, gemini_client=None) -> dict:
    with tempfile.TemporaryDirectory() as tmp_dir:
        elements, strategy = extract_elements(file_path, tmp_dir)
        sections = build_structured_output(elements, gemini_client)

    return sections