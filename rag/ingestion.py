from unstructured.partition.auto import partition
from unstructured.documents.elements import (
    Title, NarrativeText, ListItem, Table
)

def extract_elements(file_path):
    elements = partition(file_path)

    if not elements or sum(len(e.text or "") for e in elements) < 100:
        elements = partition(file_path, strategy="hi_res")

    structured_output = []

    current_section = {
        "title": None,
        "text": []
    }

    for el in elements:
        text = el.text.strip() if el.text else ""

        if not text:
            continue

        if isinstance(el, Title):
            if current_section["text"]:
                structured_output.append(current_section)

            current_section = {
                "title": text,
                "text": []
            }

        elif isinstance(el, NarrativeText):
            current_section["text"].append(text)

        elif isinstance(el, ListItem):
            current_section["text"].append(f"- {text}")

        elif isinstance(el, Table):
            current_section["text"].append(f"[TABLE]\n{text}")

    if current_section["text"]:
        structured_output.append(current_section)

    return structured_output