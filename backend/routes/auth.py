from flask import request, jsonify, Blueprint
from services.auth.auth_service import register_student, login_student
from services.sessions.sessions import get_sessions, delete_session
from flask_jwt_extended import jwt_required, get_jwt_identity
from entities.models import Session

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    response_data, status_code = register_student(data)
    return jsonify(response_data), status_code

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    response_data, status_code = login_student(data)
    
    return jsonify(response_data), status_code

@auth_bp.route('/sessions/<int:id_etudiant>', methods=['GET'])
@jwt_required()
def get_student_sessions(id_etudiant):
    current_user_id = int(get_jwt_identity())
    if current_user_id != id_etudiant:
        return jsonify({"message": "Access denied"}), 403
        
    sessions = get_sessions(id_etudiant)
    sessions_data = [session.to_dict() for session in sessions]
    return jsonify(sessions_data), 200

@auth_bp.route('/deleteSession/<int:id_session>', methods=['DELETE']) 
@jwt_required()  
def delete_student_session(id_session):
    current_user_id = int(get_jwt_identity())
    session_obj = Session.query.get(id_session)
    
    if not session_obj:
        return jsonify({"message": "Session not found"}), 404
        
    if session_obj.id_etudiant != current_user_id:
        return jsonify({"message": "Access denied"}), 403
        
    session = delete_session(int(id_session))
    if session:
        return jsonify(session.to_dict()), 200
    return jsonify({"message": "Error deleting session"}), 500
