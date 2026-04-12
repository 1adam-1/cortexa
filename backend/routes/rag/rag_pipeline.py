from flask import request, jsonify, Blueprint
from services.rag.ingestion.ingestion import save_file, extract_text
from services.rag.ingestion.chunking import chunk_text_by_tokens
from services.rag.ingestion.embedding import compute_embeddings, create_faiss_index
from entities.models import Document, Etudiant
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.rag.ingestion.load_model import load_generation_model, load_embedding_models
from services.rag.ingestion.embedding import save_chunks, save_index

pipeline_rag_bp = Blueprint("pipeline_rag", __name__)

#load models
print("loading models...")
embedding_model, reranker = load_embedding_models()
tokenizer, generation_model = load_generation_model()
print("models loaded")

#upload file
@pipeline_rag_bp.route("/api/upload", methods=["POST"])
@jwt_required()
def upload_file():
    if "file" not in request.files:
        return jsonify ({"message": "No file part"}), 400
    
    file = request.files["file"]
    
    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400

    current_user_id = get_jwt_identity()
    etudiant = Etudiant.query.get(current_user_id)

    data, code = save_file(file, etudiant)
    return jsonify(data), code


#processing file
@pipeline_rag_bp.route("/api/processing", methods=["POST"])
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
    
    
    
