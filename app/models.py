from app import db
from datetime import datetime

class Text(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(20), nullable=False)  # 'human' or 'ai'
    topic = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255))  # Path to uploaded file
    analysis = db.relationship('AnalysisResult', backref='text', lazy=True, uselist=False)

class AnalysisResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text_id = db.Column(db.Integer, db.ForeignKey('text.id'), nullable=False)
    perplexity = db.Column(db.Float)
    burstiness = db.Column(db.Float)
    ai_proportion = db.Column(db.Float)
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)