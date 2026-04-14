from entities.models import Session, db

def get_sessions(id_etudiant):
    sessions = Session.query.filter_by(id_etudiant=id_etudiant).all()
    return sessions

def get_session(id_session):
    session = Session.query.get(id_session)
    return session

def delete_session(id_session):
    session = Session.query.get(id_session)
    db.session.delete(session)
    db.session.commit()
    return session
