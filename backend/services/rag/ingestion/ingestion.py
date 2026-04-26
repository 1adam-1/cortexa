from unstructured.partition.auto import partition
import os
from werkzeug.utils import secure_filename
from unstructured.documents.elements import Title, NarrativeText, ListItem, Table
import logging
from entities.models import Session, Document, db

UPLOAD_FOLDER= './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_file(file, etudiant):
    #create a new session for the etudiant
    new_session = Session(id_etudiant=etudiant.id)
    db.session.add(new_session)
    db.session.commit()

    #save the file
    filename=secure_filename(file.filename)
    filepath=os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

     #create a new document for the session
    new_document = Document(id_session=new_session.id, title=file.filename, path=filepath)
    db.session.add(new_document)
    db.session.commit() 

    return{
        "message": "file saved successfully",
        "filepath": filepath,
        "id_document": new_document.id,
        "id_session": new_session.id

    }, 200

def extract_text(file_path: str):
    try:
        elements = partition(file_path)
    except Exception as e:
        logging.error(f"Fast partition failed for {file_path}: {e}")
        elements = []

    if not elements or sum(len(e.text or "") for e in elements) < 100:
        try:
            elements = partition(file_path, strategy="hi_res")
        except Exception as e:
            logging.error(f"hi_res partition also failed for {file_path}: {e}")
            return []

    structured_output = []
    current_section = {
        "title": "PREAMBLE",
        "types": set(),
        "content": [],
        "pages": set(),
    }

    for el in elements:
        text = el.text.strip() if el.text else ""
        if not text:
            continue

        page = el.metadata.page_number if hasattr(el, 'metadata') and hasattr(el.metadata, 'page_number') and el.metadata.page_number else None

        if isinstance(el, Title):
            if current_section["content"]:
                current_section["types"] = list(current_section["types"])
                current_section["pages"] = list(current_section["pages"])
                structured_output.append(current_section)
            current_section = {
                "title": text,
                "types": set(),
                "content": [],
                "pages": set(),
            }
            if page:
                current_section["pages"].add(page)

        elif isinstance(el, NarrativeText):
            current_section["content"].append(text)
            current_section["types"].add("NarrativeText")
            if page:
                current_section["pages"].add(page)

        elif isinstance(el, ListItem):
            current_section["content"].append(f"- {text}")
            current_section["types"].add("ListItem")
            if page:
                current_section["pages"].add(page)

        elif isinstance(el, Table):
            current_section["content"].append(f"[TABLE]\n{text}")
            current_section["types"].add("Table")
            if page:
                current_section["pages"].add(page)

    if current_section["content"]:
        current_section["types"] = list(current_section["types"])
        current_section["pages"] = list(current_section["pages"])
        structured_output.append(current_section)

    return structured_output


