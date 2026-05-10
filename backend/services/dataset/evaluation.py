import os
import json
import sys

# Add backend path for imports
_backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)

from entities.models import Document, Concept, Chunk, Cluster, db
import faiss
from services.rag.ingestion.load_model import load_generation_model, load_embedding_models
from services.rag.retrieval.retrieval import retrieve_top_chunks, rerank_unified
from services.rag.generation.generation import  generate_answer, build_context, extract_json_from_llama_response




def generate_predictions(testset_path="../../evaluation/testset.json", output_path="../../evaluation/predictions.json"):
    embedding_model, reranker_model = load_embedding_models()
    tokenizer, generation_model = load_generation_model()

    if not os.path.exists(testset_path):
        raise ValueError(f"Testset file not found: {testset_path}")
        return
    
    with open(testset_path, "r", encoding="utf-8") as f:
        testset = json.load(f)
    
    predictions = []

    for i, sample in enumerate(testset['samples']):
        question=sample['user_input']
        ground_truth=sample['reference']

        unique_documents_ids = testset.get("document_ids", [])

        final_retrieved = []
        # Utiliser les document_ids qui sont dans le JSON de test
        for doc_id in unique_documents_ids:
            index_path = f"../../uploads/index_{doc_id}.faiss"
            if not os.path.exists(index_path):
                continue
            index = faiss.read_index(index_path)
            chunks = Chunk.query.filter_by(id_document=doc_id).all()
            retrieved_chunks = retrieve_top_chunks(question, index, chunks, embedding_model)
            final_retrieved.extend(retrieved_chunks)
        
       
        documents = Document.query.filter(Document.id.in_(unique_documents_ids)).all()
        session_ids = [d.id_session for d in documents]
        concepts = Concept.query.join(Cluster).filter(Cluster.id_session.in_(session_ids)).all()

        all_candidates = final_retrieved + concepts
        reranked_candidates = rerank_unified(question, all_candidates, reranker_model)
        context = build_context(reranked_candidates, tokenizer, question, type="qa")

        answer = ""
        for chunk in generate_answer(context, question, tokenizer, generation_model, type="qa"):
            answer += chunk
        
        my_contexts = [item.content if hasattr(item, 'content') else item.definition for item in reranked_candidates]

        predictions.append({
            "question": question,
            "ground_truth": ground_truth,
            "answer": answer.strip(),
            "contexts": my_contexts
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Terminé ! Prédictions sauvegardées dans {output_path}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    from flask import Flask
    
    app = Flask(__name__)
    load_dotenv(dotenv_path=os.path.join(_backend_path, ".env"))
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        generate_predictions()
        

    