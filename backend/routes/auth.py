from flask import request, jsonify, Blueprint
from services.auth_service import register_student, login_student

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
