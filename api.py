import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from flask_cors import CORS

from rag.chunking import chunk_text_by_tokens
from rag.embeddings import compute_embeddings, load_embedding_models
from rag.ingestion import extract_elements
from storage.index import create_faiss_index, save_chunks, save_index
from app.cli import load_generation_model

app = Flask(__name__)
CORS(app)

upload_folder = 'storage'
os.makedirs(upload_folder, exist_ok=True)
app.config['UPLOAD_FOLDER'] = upload_folder


print("Chargement des modèles RAG en cours...")
tokenizer, generation_model = load_generation_model()
embedding_model, reranker = load_embedding_models()
print("Modèles chargés avec succès !")

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier n'a été envoyé"}), 400
        
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Aucun fichier sélectionné"}), 400
        
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            print(f"Extraction du texte pour {filename}...")
            sections = extract_elements(filepath)
            chunks = chunk_text_by_tokens(sections, tokenizer, max_tokens=500, min_tokens=50, overlap=50)
            
            print("Calcul des embeddings...")
            chunk_embeddings = compute_embeddings([c for c in chunks], embedding_model)
            
            print("Création de l'index FAISS...")
            index = create_faiss_index(chunk_embeddings)
            
            index_path = os.path.join(app.config['UPLOAD_FOLDER'], "index.faiss")
            chunks_path = os.path.join(app.config['UPLOAD_FOLDER'], "chunks.pkl")
            
            save_index(index, index_path)
            save_chunks(chunks, chunks_path)
            
            return jsonify({
                "message": f"Fichier {filename} indexé avec succès !",
                "chunks_count": len(chunks)
            }), 200
            
        except Exception as e:
            print(f"Erreur RAG: {e}")
            return jsonify({"error": f"Erreur lors du traitement RAG: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=False, port=5000)