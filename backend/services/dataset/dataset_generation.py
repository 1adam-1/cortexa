from __future__ import annotations

import json
import logging
import os
import sys

# Backend root must be on path before `entities` (script dir is services/dataset).
_backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)

from dotenv import load_dotenv
from flask import Flask
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document as LangchainDocument
from langchain_community.chat_models import ChatOllama
import torch

from entities.models import Chunk, Document, db
from ragas.testset import TestsetGenerator


def load_chunks_as_langchain_docs(document_ids: list) -> list[LangchainDocument]:
    """
    Load stored chunks as LangChain documents (same units your RAG indexes).
    """
    docs = []
    for doc_id in document_ids:
        chunks = Chunk.query.filter_by(id_document=doc_id).all()
        for chunk in chunks:
            docs.append(
                LangchainDocument(
                    page_content=chunk.content,
                    metadata={
                        "document_id": doc_id,
                        "chunk_id": chunk.id,
                        "title": chunk.title or "",
                        "pages": chunk.source_page or "",
                        "token_count": chunk.token_count or 0,
                    },
                )
            )
    logging.info(
        "Loaded %s chunks for document id(s) %s (requested %s doc id(s))",
        len(docs),
        document_ids,
        len(document_ids),
    )
    return docs


def document_chunk_counts() -> list[tuple[int, str | None, int]]:
    """(document_id, title, chunk_count) for every row in `document`, ordered by id."""
    rows: list[tuple[int, str | None, int]] = []
    for doc in Document.query.order_by(Document.id).all():
        n = Chunk.query.filter_by(id_document=doc.id).count()
        rows.append((doc.id, doc.title, n))
    return rows


def document_ids_with_chunks() -> list[int]:
    return [doc_id for doc_id, _title, n in document_chunk_counts() if n > 0]


def create_ragas_llm_and_embeddings():
    llm = ChatOllama(
        model="mistral-nemo",
        temperature=0.3,
        format="json"
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    return llm, embeddings


def generate_testset(
    document_ids: list,
    test_size: int = 25,
    output_path: str = "./evaluation/testset.json",
    batch_size: int = 5,
) -> dict:
    
    docs = load_chunks_as_langchain_docs(document_ids)
    if len(docs) < 10:
        raise ValueError(f"Not enough chunks: {len(docs)}. Need at least 10.")

    llm, embeddings = create_ragas_llm_and_embeddings()
    generator = TestsetGenerator.from_langchain(llm, embeddings)

    errors: list[str] = []
    samples = []
    
    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    def save_current_state(current_samples, current_errors):
        result = {
            "total": len(current_samples),
            "requested_test_size": test_size,
            "document_ids": document_ids,
            "samples": current_samples,
            "errors": current_errors,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return result

    remaining_size = test_size
    try:
        while remaining_size > 0:
            current_batch = min(remaining_size, batch_size)
            logging.info("Generating batch of %d samples (remaining: %d)...", current_batch, remaining_size)
            try:
                testset = generator.generate_with_chunks(
                    chunks=docs,
                    testset_size=current_batch,
                    raise_exceptions=False,
                )
                
                rows = testset.to_list() if testset is not None else []
                for row in rows:
                    samples.append(
                        {
                            "user_input": row.get("user_input"),
                            "reference": row.get("reference"),
                            "reference_contexts": row.get("reference_contexts"),
                            "retrieved_contexts": row.get("retrieved_contexts"),
                            "synthesizer_name": row.get("synthesizer_name"),
                        }
                    )
                
                # Symmetrical save during the process so partial progress is stored
                save_current_state(samples, errors)

            except Exception as e:
                errors.append(str(e))
                break # On hard exception, break out of batch loop
                
            remaining_size -= current_batch

    except KeyboardInterrupt:
        logging.warning("Process interrupted by user (Ctrl+C). Saving generated samples so far...")
        errors.append("Interrupted by user (KeyboardInterrupt)")

    # Final wrap up
    result = save_current_state(samples, errors)

    logging.info("Testset saved: %s samples → %s", len(samples), output_path)
    if errors:
        logging.warning("Generation completed with errors/interruptions: %s", errors)
    return result


def _parse_doc_ids_env(raw: str | None) -> list[int] | None:
    if not raw or not raw.strip():
        return None
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return [int(p) for p in parts]


# Used when RAGAS_DOC_IDS is not set. Override per machine or use env: RAGAS_DOC_IDS=55,56,57
DEFAULT_RAGAS_DOCUMENT_IDS: list[int] = [55, 56, 67, 68]


if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.join(_backend_path, "../.env"))
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    list_only = "--list-docs" in sys.argv

    with app.app_context():
        logging.basicConfig(level=logging.INFO)

        if list_only:
            print("document_id | chunks | title")
            print("------------+--------+------")
            for doc_id, title, n in document_chunk_counts():
                print(f"{doc_id:11d} | {n:6d} | {title or ''}")
            print()
            with_chunks = document_ids_with_chunks()
            print("IDs with at least one chunk:", with_chunks if with_chunks else "(none)")
            sys.exit(0)

        doc_ids = _parse_doc_ids_env(os.environ.get("RAGAS_DOC_IDS"))
        if doc_ids is None:
            doc_ids = (
                DEFAULT_RAGAS_DOCUMENT_IDS
                if DEFAULT_RAGAS_DOCUMENT_IDS
                else document_ids_with_chunks()
            )

        if not doc_ids:
            print(
                "No documents with chunks found. Run /api/processing on your files first, "
                "or set RAGAS_DOC_IDS=1,2,3 to explicit ids. Use --list-docs to see counts."
            )
            sys.exit(1)

        try:
            result = generate_testset(document_ids=doc_ids, test_size=45)
            print(
                f"Done. Used document id(s): {doc_ids}. "
                f"Generated {result['total']}/{result['requested_test_size']} sample(s)."
            )
            if result["errors"]:
                print(f"Completed with errors (partial output saved): {result['errors']}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
