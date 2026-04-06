from unstructured.partition.auto import partition
from unstructured.documents.elements import Title, NarrativeText, ListItem, Table
import logging

logger = logging.getLogger(__name__)

def extract_elements(file_path: str) -> list[dict]:
    try:
        elements = partition(file_path)
    except Exception as e:
        logger.error(f"Fast partition failed for {file_path}: {e}")
        elements = []

    if not elements or sum(len(e.text or "") for e in elements) < 100:
        try:
            elements = partition(file_path, strategy="hi_res")
        except Exception as e:
            logger.error(f"hi_res partition also failed for {file_path}: {e}")
            return []

    structured_output = []
    current_section = {
        "title": "PREAMBLE",
        "types": set(),
        "text": [],
        "pages": set(),
    }

    for el in elements:
        text = el.text.strip() if el.text else ""
        if not text:
            continue

        page = el.metadata.page_number if hasattr(el, 'metadata') and hasattr(el.metadata, 'page_number') and el.metadata.page_number else None

        if isinstance(el, Title):
            if current_section["text"]:
                current_section["types"] = list(current_section["types"])
                current_section["pages"] = list(current_section["pages"])
                structured_output.append(current_section)
            current_section = {
                "title": text,
                "types": set(),
                "text": [],
                "pages": set(),
            }
            if page:
                current_section["pages"].add(page)

        elif isinstance(el, NarrativeText):
            current_section["text"].append(text)
            current_section["types"].add("NarrativeText")
            if page:
                current_section["pages"].add(page)

        elif isinstance(el, ListItem):
            current_section["text"].append(f"- {text}")
            current_section["types"].add("ListItem")
            if page:
                current_section["pages"].add(page)

        elif isinstance(el, Table):
            current_section["text"].append(f"[TABLE]\n{text}")
            current_section["types"].add("Table")
            if page:
                current_section["pages"].add(page)

    if current_section["text"]:
        current_section["types"] = list(current_section["types"])
        current_section["pages"] = list(current_section["pages"])
        structured_output.append(current_section)

    return structured_output