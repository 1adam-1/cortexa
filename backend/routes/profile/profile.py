from flask import request, jsonify, Blueprint
from services.profile.users import update_user_profile, get_user_by_id, delete_user
from flask_jwt_extended import jwt_required, get_jwt_identity


profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = int(get_jwt_identity())
    user = get_user_by_id(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    return jsonify({
        "id": user.id,
        "nom": user.nom,
        "prenom": user.prenom,
        "email": user.email
    }), 200
    


@profile_bp.route('/update', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    updated_user, error = update_user_profile(current_user_id, data)

    if error:
        message, status_code = error
        return {"message": message}, status_code

    return {
        "message": "Profile updated successfully",
        "user": {
            "id": updated_user.id,
            "nom": updated_user.nom,
            "prenom": updated_user.prenom,
            "email": updated_user.email
        }
    }, 200

@profile_bp.route('/delete', methods=['DELETE'])
@jwt_required()
def delete_profile():
    current_user_id = int(get_jwt_identity())
    deleted = delete_user(current_user_id)
    
    if not deleted:
        return {"message": "User not found"}, 404
    
    return {"message": "Profile deleted successfully"}, 200
