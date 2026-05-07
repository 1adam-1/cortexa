from flask import json, request, jsonify, Blueprint
from services.rag.ingestion.ingestion import save_file, extract_text, create_gemini_client
from services.rag.ingestion.chunking import chunk_text_by_tokens
from services.rag.ingestion.embedding import compute_embeddings, create_faiss_index
from services.rag.generation.generation import  generate_answer, build_context, extract_json_from_llama_response
from services.rag.retrieval.retrieval import retrieve_top_chunks, rerank_chunks, rerank_unified
from entities.models import Document, Etudiant
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.rag.ingestion.load_model import load_generation_model, load_embedding_models
from services.rag.ingestion.embedding import  save_index
from entities.models import Chunk, Session, Document, Chat_message, Generation, Cluster, Cluster_chunk, Concept,Rag_context_chunk,Rag_context_concept, db
import faiss
from flask import Response, stream_with_context
from services.rag.clustering.clustering import build_cluster_context, compute_concept_embeddings, create_concept_faiss_index, extract_concept_from_clusters, cluster_chunks
import re


pipeline_rag_bp = Blueprint("pipeline_rag", __name__)

#load models
print("loading models...")
embedding_model, reranker = load_embedding_models()
tokenizer, generation_model = load_generation_model()
gemini_client = create_gemini_client()
print("models loaded")

#upload file
@pipeline_rag_bp.route("/api/upload", methods=["POST"])
@jwt_required()
def upload_file():
    id_session = request.form.get("id_session", None)
    if "file" not in request.files:
        return jsonify ({"message": "No file part"}), 400
    
    file = request.files["file"]
    
    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400

    current_user_id = get_jwt_identity()
    etudiant = Etudiant.query.get(current_user_id)

    data, code = save_file(file, etudiant, id_session=id_session)
    return jsonify(data), code


#processing file
@pipeline_rag_bp.route("/api/processing", methods=["POST"])
@jwt_required()
def processing_file():
    data = request.get_json()
    id_document = data.get("id_document")
    current_user_id = int(get_jwt_identity())

    if not id_document:
        return jsonify({"message": "No document id"}), 400
    
    document = Document.query.get(id_document)
    if not document:
        return jsonify({"message": "Document not found"}), 404
        
    # Verify ownership through session
    session_obj = Session.query.get(document.id_session)
    if not session_obj or session_obj.id_etudiant != current_user_id:
        return jsonify({"message": "Access denied"}), 403
    
    #EXTRACTING + CHUNKING + EMBEDDING + INDEXING
    path = document.path
    sections = extract_text(path, gemini_client)
    chunks = chunk_text_by_tokens(document.id, sections, tokenizer)
    embeddings = compute_embeddings(chunks, embedding_model)
    index = create_faiss_index(chunks, embeddings)
    save_index(index, f"./uploads/index_{document.id}.faiss")

    #CLUSTERING + CONCEPT EXTRACTION
    clusters, noise = cluster_chunks(chunks, embeddings)
    concepts = []
    for cluster_id, chunk_list in clusters.items():
        # Create the cluster for the database
        new_cluster = Cluster(
            id_session=document.id_session,
            method="hdbscan",
        )
        db.session.add(new_cluster)
        db.session.commit()  
        
        # Link each chunk to this new cluster
        for chunk in chunk_list:
            new_cluster_chunk = Cluster_chunk(
                id_chunk=chunk["id"],
                id_cluster=new_cluster.id,
            )
            db.session.add(new_cluster_chunk)
        db.session.commit() 

        output_str = extract_concept_from_clusters(chunk_list, generation_model, tokenizer, cluster_id)
        
        parsed_concepts = []
        try:
            match = re.search(r'\{.*\}', output_str, re.DOTALL)
            if match:
                parsed_output = json.loads(match.group(0))
                parsed_concepts = parsed_output.get("concepts", [])
        except Exception as e:
            print(f"Error parsing concept JSON: {e}")

        added_concepts = []
        for c in parsed_concepts:
            keywords_val = c.get("keywords", [])
            importance_val = c.get("importance", 0.0)
            
            new_concept = Concept(
                id_cluster=new_cluster.id,
                name=c.get("name", "Unknown"),
                definition=c.get("definition", ""),
                keywords=", ".join(keywords_val) if isinstance(keywords_val, list) else str(keywords_val),
                importance=str(importance_val),
            )
            db.session.add(new_concept)
            added_concepts.append(new_concept)
            
        db.session.flush() 
        
        concepts_ids = [c.id for c in added_concepts]
        
        if parsed_concepts:
            concept_embeddings = compute_concept_embeddings(parsed_concepts, embedding_model)
            concept_index = create_concept_faiss_index(concept_embeddings, concepts_ids)
            if concept_index is not None:
                save_index(concept_index, f"./uploads/concept_index_{new_cluster.id}.faiss")
        db.session.commit()

           

    return jsonify({"message": "Document processed successfully"}), 200


#Q/A
@pipeline_rag_bp.route("/api/chat", methods=["POST"])
@jwt_required()
def user_chat():
    data = request.get_json()
    question = data.get("message")
    session_id = data.get("session_id")
    current_user_id = int(get_jwt_identity())

    session_obj = Session.query.get(session_id)
    if not session_obj or session_obj.id_etudiant != current_user_id:
        return jsonify({"message": "Access denied"}), 403

    documents = Document.query.filter_by(id_session=session_id).all()
    if not documents:
        return jsonify({"message": "No document found for this session"}), 404

    final_retrieved_chunks=[]
    for document in documents:
        index = faiss.read_index(f"./uploads/index_{document.id}.faiss")
        chunks = Chunk.query.filter_by(id_document=document.id).all()
        retrievd_chunks = retrieve_top_chunks(question, chunks, index, embedding_model)
        final_retrieved_chunks.extend(retrievd_chunks)

    concepts = Concept.query.join(Cluster).filter(Cluster.id_session == session_id).all()
    all_candidates = final_retrieved_chunks + concepts

    reranked_items = rerank_unified(question, all_candidates, reranker)
    context = build_context(reranked_items, tokenizer, question, type="qa")

    new_chat_msg = Chat_message(
            id_session=session_id,
            content=question,
            role="user",
        )
    db.session.add(new_chat_msg)
    db.session.commit()
    chat_msg_id = new_chat_msg.id 

    context_data = []
    for item in reranked_items:
        context_data.append({
            "id": getattr(item, "id", None),
            "is_chunk": hasattr(item, "content"),
            "is_concept": hasattr(item, "definition"),
            "rerank_score": getattr(item, "rerank_score", 0.0)
        })


    def generate():
        full_answer = ""
        try:
            for chunk in generate_answer(context, question, tokenizer, generation_model, type="qa"):
                full_answer += chunk
                yield f"data: {chunk}\n\n"

        except GeneratorExit:
            print("Stream closed by client")

        finally:
            try:
                new_generation = Generation(
                    id_chat=chat_msg_id,
                    id_session=session_id,
                    type="Q/A",
                    query=question,
                    output=full_answer,
                    model=generation_model.name_or_path,
                    source="chat",
                )
                db.session.add(new_generation)
                db.session.commit()
                
                for item_data in context_data:
                    if item_data["is_chunk"]:
                        new_rag_context_chunk = Rag_context_chunk(
                            id_generation=new_generation.id,
                            id_chunk=item_data["id"],
                            reranker_model="reranker",
                            rerank_score=item_data["rerank_score"],
                        )
                        db.session.add(new_rag_context_chunk)
                    
                    elif item_data["is_concept"]:
                        new_rag_context_concept = Rag_context_concept(
                            id_generation=new_generation.id,
                            id_concept=item_data["id"],
                            similarity_score=item_data["rerank_score"],
                        )
                        db.session.add(new_rag_context_concept)
                db.session.commit()

            except Exception as e:
                print(f"Error saving generation on stop: {e}")
                db.session.rollback()
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')



#QCM
@pipeline_rag_bp.route("/api/studio/qcm", methods=["POST"])
@jwt_required()
def generate_qcm():
    data = request.get_json()
    session_id = data.get("session_id")
    num_questions = data.get("num_questions", 5)
    difficulty = data.get("difficulty", "medium")
    current_user_id = int(get_jwt_identity())
    
    question = "What are the key concepts and important facts in this document?"

    session_obj = Session.query.get(session_id)
    if not session_obj or session_obj.id_etudiant != current_user_id:
        return jsonify({"message": "Access denied"}), 403

    documents = Document.query.filter_by(id_session=session_id).all()
    if not documents:
        return jsonify({"message": "No document found for this session"}), 404

    final_retrieved_chunks=[]
    for document in documents:
        index = faiss.read_index(f"./uploads/index_{document.id}.faiss")
        chunks = Chunk.query.filter_by(id_document=document.id).all()
        retrievd_chunks = retrieve_top_chunks(question, chunks, index, embedding_model)
        final_retrieved_chunks.extend(retrievd_chunks)

    concepts = Concept.query.join(Cluster).filter(Cluster.id_session == session_id).all()
    all_candidates = final_retrieved_chunks + concepts

    reranked_items = rerank_unified(question, all_candidates, reranker)
    context = build_context(reranked_items, tokenizer, question, type="qcm", num_questions=num_questions, difficulty=difficulty)

    qcm_raw_output = ""
    for chunk in generate_answer(context, question, tokenizer, generation_model, type="qcm", num_questions=num_questions, difficulty=difficulty):
        qcm_raw_output += chunk

    parsed_qcm = extract_json_from_llama_response(qcm_raw_output)

    if not parsed_qcm:
       return jsonify({"message": "Failed to generate valid QCM format", "raw": qcm_raw_output}), 500

    new_generation = Generation(
        id_session=session_id,
        id_chat=None,
        type="QCM",
        query=question,
        output=json.dumps(parsed_qcm),
        model=generation_model.name_or_path,
        source="studio",
    )
    db.session.add(new_generation)
    db.session.commit()

    for item in reranked_items:
        if hasattr(item, "content"): 
            new_rag_context_chunk = Rag_context_chunk(
                id_generation=new_generation.id,
                id_chunk=item.id,
                reranker_model="reranker",
                rerank_score=getattr(item, "rerank_score", 0.0),
            )
            db.session.add(new_rag_context_chunk)
        
        elif hasattr(item, "definition"): 
            
            new_rag_context_concept = Rag_context_concept(
                id_generation=new_generation.id,
                id_concept=item.id,
                similarity_score=getattr(item, "rerank_score", 0.0),
            )
            db.session.add(new_rag_context_concept)
            
    db.session.commit()

    return jsonify({"qcm": parsed_qcm}), 200



# PRACTICE: Generate a single question
@pipeline_rag_bp.route("/api/studio/practice/question", methods=["POST"])
@jwt_required()
def generate_practice_question():
    data = request.get_json()
    session_id = data.get("session_id")
    
    topic = data.get("topic", "What are the key concepts and important facts in this document?")
    current_user_id = int(get_jwt_identity())

    session_obj = Session.query.get(session_id)
    if not session_obj or session_obj.id_etudiant != current_user_id:
        return jsonify({"message": "Access denied"}), 403

    documents = Document.query.filter_by(id_session=session_id).all()
    if not documents:
        return jsonify({"message": "No document found for this session"}), 404

    final_retrieved_chunks=[]
    for document in documents:
        index = faiss.read_index(f"./uploads/index_{document.id}.faiss")
        chunks = Chunk.query.filter_by(id_document=document.id).all()
        retrievd_chunks = retrieve_top_chunks(topic, chunks, index, embedding_model)
        final_retrieved_chunks.extend(retrievd_chunks)

    concepts = Concept.query.join(Cluster).filter(Cluster.id_session == session_id).all()
    all_candidates = final_retrieved_chunks + concepts

    reranked_items = rerank_unified(topic, all_candidates, reranker)
    context = build_context(reranked_items, tokenizer, topic, type="practice_question")

    question_raw_output = ""
    for chunk in generate_answer(context, topic, tokenizer, generation_model, type="practice_question"):
        question_raw_output += chunk

    question_clean = question_raw_output.strip()

    new_generation = Generation(
        id_session=session_id,
        id_chat=None,
        type="Practice_Question",
        query=topic,
        output=question_clean,
        model=generation_model.name_or_path,
        source="studio",
    )
    db.session.add(new_generation)
    db.session.commit()

    for item in reranked_items:
        if hasattr(item, "content"): 
            new_rag_context_chunk = Rag_context_chunk(
                id_generation=new_generation.id,
                id_chunk=item.id,
                reranker_model="reranker",
                rerank_score=getattr(item, "rerank_score", 0.0),
            )
            db.session.add(new_rag_context_chunk)
        
        elif hasattr(item, "definition"): 
            new_rag_context_concept = Rag_context_concept(
                id_generation=new_generation.id,
                id_concept=item.id,
                similarity_score=getattr(item, "rerank_score", 0.0),
            )
            db.session.add(new_rag_context_concept)
            
    db.session.commit()

    return jsonify({"question": question_clean}), 200


# PRACTICE: Evaluate the user's answer
@pipeline_rag_bp.route("/api/studio/practice/evaluate", methods=["POST"])
@jwt_required()
def evaluate_practice_answer():
    data = request.get_json()
    session_id = data.get("session_id")
    question = data.get("question")
    user_answer = data.get("user_answer")
    current_user_id = int(get_jwt_identity())

    if not question or not user_answer:
        return jsonify({"message": "Question and user_answer are required"}), 400

    session_obj = Session.query.get(session_id)
    if not session_obj or session_obj.id_etudiant != current_user_id:
        return jsonify({"message": "Access denied"}), 403

    documents = Document.query.filter_by(id_session=session_id).all()
    if not documents:
        return jsonify({"message": "No document found for this session"}), 404

    final_retrieved_chunks=[]
    for document in documents:
        index = faiss.read_index(f"./uploads/index_{document.id}.faiss")
        chunks = Chunk.query.filter_by(id_document=document.id).all()
        retrievd_chunks = retrieve_top_chunks(question, chunks, index, embedding_model)
        final_retrieved_chunks.extend(retrievd_chunks)

    concepts = Concept.query.join(Cluster).filter(Cluster.id_session == session_id).all()
    all_candidates = final_retrieved_chunks + concepts

    reranked_items = rerank_unified(question, all_candidates, reranker)
    
    # We pass the question + the user answer to the prompt
    eval_query = f"Question: {question}\nUser's Answer: {user_answer}"
    context = build_context(reranked_items, tokenizer, eval_query, type="practice_evaluation")

    eval_raw_output = ""
    for chunk in generate_answer(context, eval_query, tokenizer, generation_model, type="practice_evaluation"):
        eval_raw_output += chunk

    parsed_eval = extract_json_from_llama_response(eval_raw_output)

    if not parsed_eval:
       return jsonify({"message": "Failed to generate valid evaluation format", "raw": eval_raw_output}), 500

    new_generation = Generation(
        id_session=session_id,
        id_chat=None,
        type="Practice_Evaluation",
        query=eval_query,
        output=json.dumps(parsed_eval),
        model=generation_model.name_or_path,
        source="studio",
    )
    db.session.add(new_generation)
    db.session.commit()

    for item in reranked_items:
        if hasattr(item, "content"): 
            new_rag_context_chunk = Rag_context_chunk(
                id_generation=new_generation.id,
                id_chunk=item.id,
                reranker_model="reranker",
                rerank_score=getattr(item, "rerank_score", 0.0),
            )
            db.session.add(new_rag_context_chunk)
        
        elif hasattr(item, "definition"): 
            new_rag_context_concept = Rag_context_concept(
                id_generation=new_generation.id,
                id_concept=item.id,
                similarity_score=getattr(item, "rerank_score", 0.0),
            )
            db.session.add(new_rag_context_concept)
            
    db.session.commit()

    return jsonify({"evaluation": parsed_eval}), 200


#SUMMARY
@pipeline_rag_bp.route("/api/studio/summary", methods=["POST"])
@jwt_required()
def generate_summary():
    data = request.get_json()
    session_id = data.get("session_id")
    topic = data.get("topic", "What are the key concepts and important facts in this document?")
    current_user_id = int(get_jwt_identity())

    session_obj = Session.query.get(session_id)
    if not session_obj or session_obj.id_etudiant != current_user_id:
        return jsonify({"message": "Access denied"}), 403
    
    documents = Document.query.filter_by(id_session=session_id).all()
    if not documents:
        return jsonify({"message": "No document found for this session"}), 404
    
    final_retrieved_chunks=[]
    for document in documents:
        index = faiss.read_index(f"./uploads/index_{document.id}.faiss")
        chunks = Chunk.query.filter_by(id_document=document.id).all()
        retrievd_chunks = retrieve_top_chunks(topic, chunks, index, embedding_model)
        final_retrieved_chunks.extend(retrievd_chunks)
    
    concepts = Concept.query.join(Cluster).filter(Cluster.id_session == session_id).all()
    all_candidates = final_retrieved_chunks + concepts
    reranked_items = rerank_unified(topic, all_candidates, reranker)
    context = build_context(reranked_items, tokenizer, topic, type="summary")

    summary_raw_output = ""
    for chunk in generate_answer(context, topic, tokenizer, generation_model, type="summary"):
        summary_raw_output += chunk
    
    if not summary_raw_output.strip():
        return jsonify({"message": "Failed to generate a summary", "raw": summary_raw_output}), 500
    
    new_generation = Generation(
        id_session=session_id,
        id_chat=None,
        type="Summary",
        query=topic,
        output=summary_raw_output.strip(),
        model=generation_model.name_or_path,
        source="studio",
    )
    db.session.add(new_generation)
    db.session.commit()

    for item in reranked_items:
        if hasattr(item, "content"):
            new_rag_context_chunk = Rag_context_chunk(
                id_generation=new_generation.id,
                id_chunk=item.id,
                reranker_model="reranker",
                rerank_score=getattr(item, "rerank_score", 0.0),
            )
            db.session.add(new_rag_context_chunk)

        elif hasattr(item, "definition"):
            new_rag_context_concept = Rag_context_concept(
                id_generation=new_generation.id,
                id_concept=item.id,
                similarity_score=getattr(item, "rerank_score", 0.0),
            )
            db.session.add(new_rag_context_concept)
    db.session.commit()

    return jsonify({"summary": summary_raw_output.strip()}), 200


#Fetching data from db

#Fetching QCM
@pipeline_rag_bp.route("/api/generation/qcm/<int:session_id>", methods=["GET"])
@jwt_required()
def get_qcm_generation(session_id):
    generations = db.session.query(Generation).filter_by(id_session=session_id, type="QCM").order_by(Generation.created_at.desc()).all()

    if not generations:
        return jsonify({"qcms": []}), 200
    
    generation_history = []
    for gen in generations:
        generation_history.append({
            "id": gen.id,
            "query": gen.query,
            "output": gen.output,
            "created_at": gen.created_at.isoformat(),
        })

    return jsonify({"qcms": generation_history}), 200


#Fetching chat history
@pipeline_rag_bp.route("/api/sessions/<int:session_id>/messages", methods=["GET"])
@jwt_required()
def get_chat_history(session_id):
    current_user_id = int(get_jwt_identity())
    session_obj = Session.query.get(session_id)
    
    if not session_obj or session_obj.id_etudiant != current_user_id:
        return jsonify({"message": "Access denied"}), 403

    messages = Chat_message.query.filter_by(id_session=session_id).order_by(Chat_message.created_at.asc()).all()
    
    history = []
    for msg in messages:
        history.append({
            "id": msg.id,
            "role": "user",
            "content": msg.content,
            "created_at": msg.created_at.isoformat()
        })
        
       
        gen = db.session.query(Generation).filter_by(id_chat=msg.id).first()
        if gen:
            history.append({
                "id": f"gen_{gen.id}",
                "role": "assistant",
                "content": gen.output,
                "created_at": gen.created_at.isoformat()
            })
            
    return jsonify(history), 200


#Fetching summaries
@pipeline_rag_bp.route("/api/generation/summary/<int:session_id>", methods=["GET"])
@jwt_required()
def get_summaries(session_id):
    generations =  db.session.query(Generation).filter_by(id_session=session_id, type="Summary").order_by(Generation.created_at.desc()).all()
    if not generations:
        return jsonify({"summaries": []}), 200
    
    summaries = []
    for gen in generations:
        summaries.append({
            "id": gen.id,
            "query": gen.query,
            "output": gen.output,
            "created_at": gen.created_at.isoformat(),
        })
    
    return jsonify({"summaries": summaries}), 200


