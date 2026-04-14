from flask import request, jsonify, Blueprint
from services.auth.auth_service import register_student, login_student
from services.sessions import get_sessions, get_session

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
def get_student_sessions(id_etudiant):
    sessions = get_sessions(id_etudiant)
    sessions_data = [session.to_dict() for session in sessions]
    return jsonify(sessions_data), 200

    