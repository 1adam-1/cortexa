from backend.entities.models import Chunk
from flask import request, jsonify, Blueprint
from services.rag.ingestion.ingestion import save_file, extract_text
from services.rag.ingestion.chunking import chunk_text_by_tokens
from services.rag.ingestion.embedding import compute_embeddings, create_faiss_index
from services.rag.generation.generation import count_tokens, generate_answer, build_context
from services.rag.retrieval.retrieval import retrieve_top_chunks, rerank_chunks
from entities.models import Document, Etudiant
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.rag.ingestion.load_model import load_generation_model, load_embedding_models
from services.rag.ingestion.embedding import save_chunks, save_index
from entities.models import Session, Document, Chat_message, Generation, db
import faiss

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
    save_index(index, f"./uploads/index_{document.id}.faiss")

    return jsonify({"message": "Document processed successfully"}), 200


#Q/A
@pipeline_rag_bp.route("/api/chat", methods=["POST"])
def user_chat():
    data = request.get_json()
    question = data.get("message")
    session_id = data.get("session_id")
    document = Document.query.get(id_session=session_id)

    index = faiss.read_index(f"./uploads/index_{document.id}.faiss")
    chunks = Chunk.query.filter_by(id_document=document.id).all()

    retrievd_chunks = retrieve_top_chunks(question, index, chunks, embedding_model)
    reranked_chunks = rerank_chunks(question, retrievd_chunks, reranker)
    context = build_context(reranked_chunks, tokenizer, question)
    answer = generate_answer(context, question, tokenizer, generation_model)

    new_chat_msg = Chat_message(
        id_session=session_id,
        content=question,
        role="user",
    )
    db.session.add(new_chat_msg)
    db.session.commit()

    new_generation = Generation(
        id_chat_message=new_chat_msg.id,
        id_session=session_id,
        type="Q/A",
        query=question,
        output=answer,
        model=generation_model.name_or_path,
        source="chat",
    )
    db.session.add(new_generation)
    db.session.commit()

    return jsonify({"answer": answer}), 200
    
    




    

    
    
    
