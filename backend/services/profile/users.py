import re
from entities.models import Etudiant, db

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def get_user_by_id(user_id):
    user = Etudiant.query.get(user_id)
    return user

def update_user_profile(user_id, data):
    user = Etudiant.query.get(user_id)
    if not user:
        return None, ("User not found", 404)

    email = data.get('email')
    if email is not None:
        email = email.strip()
        if not EMAIL_RE.match(email):
            return None, ("Invalid email format", 400)
        taken = Etudiant.query.filter(Etudiant.email == email, Etudiant.id != user_id).first()
        if taken:
            return None, ("Email already in use", 400)
        user.email = email

    user.nom = data.get('nom', user.nom)
    user.prenom = data.get('prenom', user.prenom)

    db.session.commit()
    return user, None

def delete_user(user_id):
    user = Etudiant.query.get(user_id)
    if not user:
        return None

    db.session.delete(user)
    db.session.commit()
    return user
