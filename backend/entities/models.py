from sqlalchemy import ForeignKey
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Etudiant(db.Model):
    __tablename__ = "etudiant"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)


class Session(db.Model):
    __tablename__ = "session"

    id=db.Column(db.Integer, primary_key=True)
    id_etudiant=db.Column(db.Integer, ForeignKey("etudiant.id", ondelete='CASCADE'), nullable=False)
    date_debut=db.Column(db.DateTime, default=datetime.utcnow)
    etudiant=db.relationship("Etudiant", backref=db.backref("sessions", cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "id_etudiant": self.id_etudiant,
            "date_debut": self.date_debut.isoformat() if self.date_debut else None,
            "documents": [doc.to_dict() for doc in self.documents] if hasattr(self, 'documents') else []
        }


class Document(db.Model):
    __tablename__ = "document"

    id=db.Column(db.Integer, primary_key=True)
    id_session=db.Column(db.Integer, ForeignKey("session.id", ondelete='CASCADE'), nullable=False)
    title=db.Column(db.String(400), nullable=True)
    path=db.Column(db.String(400), nullable=True)
    date_upload=db.Column(db.DateTime, default=datetime.utcnow)
    session=db.relationship("Session", backref=db.backref("documents", cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "path": self.path,
            "date_upload": self.date_upload.isoformat() if self.date_upload else None
        }


class Chunk(db.Model):
    __tablename__ = "chunk"

    id=db.Column(db.Integer, primary_key=True)
    id_document=db.Column(db.Integer, ForeignKey("document.id", ondelete='CASCADE'), nullable=False)
    title=db.Column(db.String(100), nullable=False)
    content=db.Column(db.Text, nullable=False)
    type=db.Column(db.String(100), nullable=False)
    token_count=db.Column(db.Integer, nullable=False)
    source_page=db.Column(db.String(100), nullable=True)
    document=db.relationship("Document", backref=db.backref("chunks", cascade="all, delete-orphan"))


class Chunk_embedding(db.Model):
    __tablename__ = "chunk_embedding"

    id=db.Column(db.Integer, primary_key=True)
    id_chunk=db.Column(db.Integer, ForeignKey("chunk.id", ondelete='CASCADE'), nullable=False)
    id_faiss=db.Column(db.Integer, nullable=False)
    dimension=db.Column(db.Float, nullable=False)
    chunk=db.relationship("Chunk", backref=db.backref("chunk_embeddings", cascade="all, delete-orphan"))


class Cluster(db.Model):
    __tablename__ = "cluster"

    id=db.Column(db.Integer, primary_key=True)
    id_session=db.Column(db.Integer, ForeignKey("session.id", ondelete='CASCADE'), nullable=False)
    method=db.Column(db.String(100), nullable=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
    session=db.relationship("Session", backref=db.backref("clusters", cascade="all, delete-orphan"))


class Cluster_chunk(db.Model):
    __tablename__ = "cluster_chunk"

    id_chunk=db.Column(db.Integer, ForeignKey("chunk.id", ondelete='CASCADE'), nullable=False, primary_key=True)
    id_cluster=db.Column(db.Integer, ForeignKey("cluster.id", ondelete='CASCADE'), nullable=False, primary_key=True)


class Concept(db.Model):
    __tablename__ = "concept"

    id=db.Column(db.Integer, primary_key=True)
    id_cluster=db.Column(db.Integer, ForeignKey("cluster.id", ondelete='CASCADE'), nullable=False)
    name=db.Column(db.String(100), nullable=False)
    definition=db.Column(db.Text, nullable=False)
    keywords=db.Column(db.Text, nullable=False)
    importance=db.Column(db.Text, nullable=False)
    cluster=db.relationship("Cluster", backref=db.backref("concepts", cascade="all, delete-orphan"))


class Concept_embedding(db.Model):
    __tablename__ = "concept_embedding"

    id=db.Column(db.Integer, primary_key=True)
    id_concept=db.Column(db.Integer, ForeignKey("concept.id", ondelete='CASCADE'), nullable=False)
    id_faiss=db.Column(db.Integer, nullable=False)
    dimension=db.Column(db.Float, nullable=False)


class Chat_message(db.Model):
    __tablename__ = "chat_message"

    id=db.Column(db.Integer, primary_key=True)
    id_session=db.Column(db.Integer, ForeignKey("session.id", ondelete='CASCADE'), nullable=False)
    content=db.Column(db.Text, nullable=False)
    role=db.Column(db.String(100), nullable=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
    session=db.relationship("Session", backref=db.backref("chat_messages", cascade="all, delete-orphan"))


class Generation(db.Model):
    __tablename__ = "generation"

    id=db.Column(db.Integer, primary_key=True)
    id_session=db.Column(db.Integer, ForeignKey("session.id", ondelete='CASCADE'), nullable=False)
    id_chat=db.Column(db.Integer, ForeignKey("chat_message.id", ondelete='CASCADE'), nullable=True)
    type=db.Column(db.String(100), nullable=False)
    query=db.Column(db.Text, nullable=False)
    output=db.Column(db.Text, nullable=False)
    model=db.Column(db.String(100), nullable=False)
    source=db.Column(db.String(100), nullable=False)
    created_at=db.Column(db.DateTime, default=datetime.utcnow)
    session=db.relationship("Session", backref=db.backref("generations", cascade="all, delete-orphan"))
    chat_message=db.relationship("Chat_message", backref=db.backref("generations", cascade="all, delete-orphan"))
    


class Rag_context_chunk(db.Model):
    __tablename__ = "rag_context_chunk"

    id_generation=db.Column(db.Integer, ForeignKey("generation.id", ondelete='CASCADE'), nullable=False, primary_key=True)
    id_chunk=db.Column(db.Integer, ForeignKey("chunk.id", ondelete='CASCADE'), nullable=False, primary_key=True)
    reranker_model=db.Column(db.String(100), nullable=False)
    rerank_score=db.Column(db.Float, nullable=False)
    

class Rag_context_concept(db.Model):
    __tablename__ = "rag_context_concept"

    id_generation=db.Column(db.Integer, ForeignKey("generation.id", ondelete='CASCADE'), nullable=False, primary_key=True)
    id_concept=db.Column(db.Integer, ForeignKey("concept.id", ondelete='CASCADE'), nullable=False, primary_key=True)
    similarity_score=db.Column(db.Float, nullable=False)
    
    