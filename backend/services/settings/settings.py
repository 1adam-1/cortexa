from entities.models import User_settings, Session, Chat_message, db

ALLOWED_VALUES = {
    "theme": {"light", "dark"},
    "font_size": {"small", "medium", "large"},
    "response_length": {"concise", "balanced", "detailed"},
}

def get_or_create_settings(user_id):
    settings = User_settings.query.filter_by(id_etudiant=user_id).first()
    if not settings:
        settings = User_settings(id_etudiant=user_id)
        db.session.add(settings)
        db.session.commit()
    return settings

def update_settings(user_id, data):
    settings = get_or_create_settings(user_id)

    errors = []
    for key, allowed in ALLOWED_VALUES.items():
        if key in data:
            value = data[key]
            if value not in allowed:
                errors.append(f"{key} must be one of {sorted(allowed)}")
            else:
                setattr(settings, key, value)

    if errors:
        db.session.rollback()
        return None, errors

    db.session.commit()
    return settings, None

def clear_chat_history(user_id):
    session_ids = [s.id for s in Session.query.filter_by(id_etudiant=user_id).all()]
    if not session_ids:
        return 0

    messages = Chat_message.query.filter(Chat_message.id_session.in_(session_ids)).all()
    count = len(messages)
    for msg in messages:
        db.session.delete(msg)
    db.session.commit()
    return count
