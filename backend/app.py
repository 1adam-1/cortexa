from flask import Flask, jsonify
from entities.models import db
from flask_cors import CORS
import os 
from dotenv import load_dotenv
from routes.auth import auth_bp
from routes.evaluation import evaluation_bp
from routes.rag.rag_pipeline import pipeline_rag_bp
from routes.profile.profile import profile_bp
from routes.settings.settings import settings_bp
from flask_jwt_extended import JWTManager

load_dotenv(dotenv_path='../.env')

app=Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(pipeline_rag_bp)
app.register_blueprint(evaluation_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(settings_bp)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
jwt = JWTManager(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create any missing tables (e.g. user_settings); existing tables are untouched
with app.app_context():
    db.create_all()

@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "Welcome to Cortexa"})

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)