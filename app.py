from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, Task
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 👥 HARDCODED USERS - Change these credentials
AUTHORIZED_USERS = {
    'user1': 'password123',  # First user
    'user2': 'password456'   # Second user
}

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.query.get(int(user_id))


def init_database():
    """Initialize database with hardcoded users"""
    with app.app_context():
        db.create_all()
        
        # Create users if they don't exist
        for username, password in AUTHORIZED_USERS.items():
            existing_user = User.query.filter_by(username=username).first()
            if not existing_user:
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                new_user = User(username=username, password_hash=hashed_password)
                db.session.add(new_user)
        
        db.session.commit()
        print("✅ Database initialized with users!")


# Routes
@app.route('/')
def index():
    """Home page - redirect to login or app"""
    if current_user.is_authenticated:
        return redirect(url_for('todo_app'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('todo_app'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check if user exists
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('todo_app'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    return redirect(url_for('login'))


@app.route('/app')
@login_required
def todo_app():
    """Main todo application page"""
    return render_template('app.html', username=current_user.username)


# API Routes
@app.route('/api/tasks/personal', methods=['GET'])
@login_required
def get_personal_tasks():
    """Get personal tasks for current user"""
    tasks = Task.query.filter_by(user_id=current_user.id, is_shared=False).all()
    return jsonify([task.to_dict() for task in tasks])


@app.route('/api/tasks/shared', methods=['GET'])
@login_required
def get_shared_tasks():
    """Get shared tasks"""
    tasks = Task.query.filter_by(is_shared=True).all()
    return jsonify([task.to_dict() for task in tasks])


@app.route('/api/tasks', methods=['POST'])
@login_required
def create_task():
    """Create a new task"""
    data = request.json
    
    new_task = Task(
        text=data['text'],
        is_shared=data.get('is_shared', False),
        created_by=current_user.username,
        user_id=None if data.get('is_shared', False) else current_user.id
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    return jsonify(new_task.to_dict()), 201


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """Update a task (toggle completion)"""
    task = Task.query.get_or_404(task_id)
    
    # Check permissions
    if not task.is_shared and task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    task.completed = data.get('completed', task.completed)
    
    db.session.commit()
    
    return jsonify(task.to_dict())


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """Delete a task"""
    task = Task.query.get_or_404(task_id)
    
    # Check permissions
    if not task.is_shared and task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(task)
    db.session.commit()
    
    return '', 204


if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)