from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    # Relationship to tasks
    personal_tasks = db.relationship('Task', 
                                    foreign_keys='Task.user_id',
                                    backref='owner', 
                                    lazy=True,
                                    cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'


class Task(db.Model):
    """Task model for to-do items"""
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    is_shared = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key for personal tasks
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    def to_dict(self):
        """Convert task to dictionary"""
        return {
            'id': self.id,
            'text': self.text,
            'completed': self.completed,
            'is_shared': self.is_shared,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Task {self.text[:20]}...>'