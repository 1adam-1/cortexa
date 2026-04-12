from flask import request, jsonify, Blueprint
from backend.services.rag.ingestion.ingestion import save_file, extract_text
from backend.services.rag.ingestion.chunking import chunk_text_by_tokens
from backend.services.rag.ingestion.embedding import compute_embeddings, create_faiss_index
from backend.entities.models import Document
from backend.services.rag.ingestion.load_model import load_generation_model, load_embedding_models
from backend.services.rag.ingestion.embedding import save_chunks, save_index

pipeline_rag_bp = Blueprint("pipeline_rag", __name__)

#load models
print("loading models...")
embedding_model, reranker = load_embedding_models()
tokenizer, generation_model = load_generation_model()
print("models loaded")


@pipeline_rag_bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify ({"message": "No file part"}), 400
    
    file = request.files["file"]
    
    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400

    data, code = save_file(file)
    return jsonify(data), code

@pipeline_rag_bp.route("/processing", methods=["POST"])
def processing_file():
    

    data = request.get_json()
    id_document = data.get("id_document")

    if not id_document:
        return jsonify({"message": "No document id"}), 400
    
    document = Document.query.get(id_document)
    if not document:
        return jsonify({"message": "Document not found"}), 404
    
    path = document.path
    sections = extract_text(path)
    chunks = chunk_text_by_tokens(document.id, sections, tokenizer)
    embeddings = compute_embeddings(chunks, embedding_model)
    index = create_faiss_index(chunks, embeddings)
    save_chunks(chunks, f"chunks_{document.id}.pkl")
    save_index(index, f"index_{document.id}.faiss")

    return jsonify({"message": "Document processed successfully"}), 200
    
    
    
