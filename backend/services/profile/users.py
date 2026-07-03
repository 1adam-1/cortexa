from entities.models import Etudiant, db

def get_user_by_id(user_id):
    user = Etudiant.query.get(user_id)
    return user

def update_user_profile(user_id, data):
    user = Etudiant.query.get(user_id)
    if not user:
        return None
    
    user.nom = data.get('nom', user.nom)
    user.prenom = data.get('prenom', user.prenom)
    user.email = data.get('email', user.email)
    
    db.session.commit()
    return user    

def delete_user(user_id):   
    user = Etudiant.query.get(user_id)
    if not user:
        return None
    
    db.session.delete(user)
    db.session.commit()
    return user

