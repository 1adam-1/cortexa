import os
import json
import sys

# Add backend path for imports
_backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)

from entities.models import Document, Chunk, db
import faiss
from services.rag.ingestion.load_model import load_generation_model, load_embedding_models
from services.rag.retrieval.retrieval import retrieve_top_chunks, rerank_unified
from services.rag.generation.generation import generate_answer, build_context

# Path constants
TESTSET_JSON_PATH = os.path.join(_backend_path, "evaluation", "testset.json")
PREDICTIONS_OUTPUT_PATH = os.path.join(_backend_path, "evaluation", "predictions.json")


def generate_predictions(testset_path=None, output_path=None):
    """
    Runs the RAG pipeline on every sample in the testset and saves:
      - retrieved_contexts : list of individual chunk/concept strings (for RAGAS)
      - response           : generated answer (for RAGAS)
    The output format matches what RAGAS expects:
      user_input, reference, reference_contexts, retrieved_contexts, response
    """
    if testset_path is None:
        testset_path = TESTSET_JSON_PATH
    if output_path is None:
        output_path = PREDICTIONS_OUTPUT_PATH

    testset_path = os.path.abspath(testset_path)
    output_path = os.path.abspath(output_path)

    if not os.path.exists(testset_path):
        raise FileNotFoundError(
            f"Testset file not found: {testset_path}\n"
            "Generate it first: py .\\services\\dataset\\dataset_generation.py"
        )

    with open(testset_path, "r", encoding="utf-8") as f:
        testset = json.load(f)

    embedding_model, reranker_model, nli_model = load_embedding_models()
    tokenizer, generation_model = load_generation_model()

    unique_documents_ids = testset.get("document_ids", [])

    # Pre-load FAISS indexes and chunks once (avoid reloading per sample)
    print("Loading FAISS indexes...")
    index_map: dict[int, tuple] = {}  # doc_id -> (faiss_index, chunks_list)
    for doc_id in unique_documents_ids:
        index_path = os.path.join(_backend_path, "uploads", f"index_{doc_id}.faiss")
        if not os.path.exists(index_path):
            print(f"  [WARN] No FAISS index found for doc_id={doc_id}, skipping.")
            continue
        index = faiss.read_index(index_path)
        chunks = Chunk.query.filter_by(id_document=doc_id).all()
        index_map[doc_id] = (index, chunks)
        print(f"  Loaded doc_id={doc_id}: {len(chunks)} chunks")

    predictions = []
    total = len(testset["samples"])

    for i, sample in enumerate(testset["samples"]):
        question = sample["user_input"]
        ground_truth = sample["reference"]

        print(f"\n[{i+1}/{total}] Processing: {question[:80]}...")

        # ── 1. Retrieve ──────────────────────────────────────────────────────────
        all_candidates = []
        for doc_id, (index, chunks) in index_map.items():
            retrieved = retrieve_top_chunks(
                question, chunks, index, embedding_model,
            )
            all_candidates.extend(retrieved)

        # ── 2. Rerank ────────────────────────────────────────────────────────────
        reranked_candidates = rerank_unified(question, all_candidates, reranker_model)

        # ── 3. Extract individual chunk texts for RAGAS ──────────────────────────
        # IMPORTANT: must be individual strings, NOT one concatenated block.
        retrieved_texts = []
        for item in reranked_candidates:
            if hasattr(item, "content") and item.content:
                retrieved_texts.append(item.content)
            elif hasattr(item, "definition") and item.definition:
                retrieved_texts.append(f"{item.name}: {item.definition}")

        # ── 4. Build prompt context and generate answer ──────────────────────────
        context = build_context(reranked_candidates, tokenizer, question, type="qa")

        answer = ""
        for chunk in generate_answer(
            context, question, tokenizer, generation_model, type="qa", target_language_code="en"
        ):
            answer += chunk

        answer = answer.strip()
        print(f"  Retrieved {len(retrieved_texts)} chunks → answer: {answer[:100]}...")

        # ── 5. Store in RAGAS-compatible format ──────────────────────────────────
        predictions.append(
            {
                "user_input": question,
                "reference": ground_truth,
                "reference_contexts": sample.get("reference_contexts") or [],
                "retrieved_contexts": retrieved_texts,
                "response": answer,
            }
        )

        # Save incrementally so partial progress is not lost
        _save(predictions, output_path, testset)

    print(f"\n✅ Done! {len(predictions)}/{total} predictions saved → {output_path}")
    return predictions


def _save(predictions: list, output_path: str, testset: dict) -> None:
    """Persist current predictions to disk (called after every sample)."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result = {
        "total": len(predictions),
        "requested_test_size": testset.get("requested_test_size", len(predictions)),
        "document_ids": testset.get("document_ids", []),
        "samples": predictions,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from dotenv import load_dotenv
    from flask import Flask

    _dotenv_path = os.path.abspath(os.path.join(_backend_path, "..", ".env"))
    load_dotenv(dotenv_path=_dotenv_path)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Define it in the project root .env file "
            f"(looked for {_dotenv_path}) or set it in your environment."
        )

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        generate_predictions()