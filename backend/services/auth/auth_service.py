from werkzeug.security import generate_password_hash, check_password_hash
from entities.models import Etudiant, db
from flask_jwt_extended import create_access_token

def register_student(data):
    nom = data.get('nom')
    prenom = data.get('prenom')
    email = data.get('email')
    password = data.get('password')

    exist = Etudiant.query.filter_by(email=email).first()
    if exist:
        return {'message': 'Email already exists'}, 400

    hashed_password = generate_password_hash(password)
    new_etudiant = Etudiant(nom=nom, prenom=prenom, email=email, password=hashed_password)

    db.session.add(new_etudiant)
    db.session.commit()

    return {'message': 'User created successfully'}, 201

def login_student(data):
    email = data.get('email')
    password = data.get('password')

    exist = Etudiant.query.filter_by(email=email).first()
    if not exist or not check_password_hash(exist.password, password):
        return {'message': 'informations invalides'}, 404

    access_token = create_access_token(identity=str(exist.id))
    
    return {
        "message": "login successfully",
        "access_token": access_token,
        "user": {
            "id": exist.id,
            "nom": exist.nom,
            "prenom": exist.prenom,
            "email": exist.email
        }
    }, 200
