import os
from entities.models import Session, db

def get_sessions(id_etudiant):
    sessions = Session.query.filter_by(id_etudiant=id_etudiant).all()
    return sessions

def get_session(id_session):
    session = Session.query.get(id_session)
    return session

def delete_session(id_session):
    session = Session.query.get(id_session)
    if session:
        # Loop through all documents in this session and delete their faiss index files
        for doc in session.documents:
            faiss_path = f"./uploads/index_{doc.id}.faiss"
            if os.path.exists(faiss_path):
                try:
                    os.remove(faiss_path)
                except Exception as e:
                    print(f"Failed to delete {faiss_path}: {e}")
                    
        db.session.delete(session)
        db.session.commit()
    return session
