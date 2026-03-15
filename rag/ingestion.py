import pdfplumber

from rag.chunking import chunk_text_by_tokens


def extract_pages_from_pdf(path):
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                pages.append(
                    {
                        "text": text,
                        "source": path,
                        "page": i + 1,
                    }
                )
    return pages


def chunk_pages(pages, tokenizer):
    all_chunks = []

    for page in pages:
        chunks = chunk_text_by_tokens(page["text"], tokenizer)
        for chunk in chunks:
            all_chunks.append(
                {
                    "text": chunk,
                    "source": page["source"],
                    "page": page["page"],
                }
            )
    return all_chunks
