from flask import request, jsonify, Blueprint
from services.settings.settings import get_or_create_settings, update_settings, clear_chat_history
from flask_jwt_extended import jwt_required, get_jwt_identity


settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_settings():
    current_user_id = int(get_jwt_identity())
    settings = get_or_create_settings(current_user_id)
    return jsonify(settings.to_dict()), 200


@settings_bp.route('/settings', methods=['PUT'])
@jwt_required()
def put_settings():
    current_user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    settings, errors = update_settings(current_user_id, data)
    if errors:
        return jsonify({"message": "; ".join(errors)}), 400

    return jsonify({
        "message": "Settings updated successfully",
        "settings": settings.to_dict()
    }), 200


@settings_bp.route('/settings/chat-history', methods=['DELETE'])
@jwt_required()
def delete_chat_history():
    current_user_id = int(get_jwt_identity())
    count = clear_chat_history(current_user_id)
    return jsonify({
        "message": "Chat history cleared",
        "deleted_messages": count
    }), 200
