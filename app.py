from datetime import datetime
import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, leave_room, emit
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'chat.db')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

socketio = SocketIO(app, cors_allowed_origins="*")
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ------------------- Models -------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(80), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='user', lazy=True)
    owned_groups = db.relationship('Group', backref='owner', lazy=True)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='group', lazy=True)
    memberships = db.relationship('Membership', backref='group_obj', lazy=True)

class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='memberships', lazy=True)
    group = db.relationship('Group', backref=db.backref('members', lazy=True))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------- Routes -------------------
@app.route('/')
@login_required
def home():
    groups = Group.query.order_by(Group.created_at.desc()).all()
    return render_template('groups.html', groups=groups)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        display_name = request.form.get('display_name', '').strip()
        avatar_url = request.form.get('avatar_url', '').strip() or None
        if not email or not password or not display_name:
            flash('Please fill all required fields', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        user = User(email=email, display_name=display_name, avatar_url=avatar_url)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Welcome back!', 'success')
            return redirect(url_for('home'))
        flash('Invalid credentials', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        display_name = request.form.get('display_name', '').strip()
        avatar_url = request.form.get('avatar_url', '').strip() or None
        if display_name:
            current_user.display_name = display_name
        current_user.avatar_url = avatar_url
        db.session.commit()
        flash('Profile updated', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html')

@app.route('/groups', methods=['GET', 'POST'])
@login_required
def groups():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')

        if not name.strip():
            flash('Group name is required.', 'error')
            return redirect(url_for('groups'))

        new_group = Group(name=name, description=description, owner_id=current_user.id)
        db.session.add(new_group)
        db.session.commit()
        flash('Group created successfully!', 'success')
        return redirect(url_for('groups'))

    all_groups = Group.query.all()
    return render_template('groups.html', groups=all_groups)



@app.route('/groups/<int:group_id>/join', methods=['POST'])
@login_required
def join_group(group_id):
    if not Membership.query.filter_by(user_id=current_user.id, group_id=group_id).first():
        db.session.add(Membership(user_id=current_user.id, group_id=group_id))
        db.session.commit()
    return redirect(url_for('chat', group_id=group_id))

@app.route('/groups/<int:group_id>')
@login_required
def chat(group_id):
    group = Group.query.get_or_404(group_id)
    if not Membership.query.filter_by(user_id=current_user.id, group_id=group_id).first():
        db.session.add(Membership(user_id=current_user.id, group_id=group_id))
        db.session.commit()
    messages = Message.query.filter_by(group_id=group_id).order_by(Message.created_at).all()
    return render_template('chat.html', group=group, messages=messages)

# ------------------- SocketIO -------------------
@socketio.on('send_message')
def handle_message(data):
    group_id = data.get('group_id')
    content = data.get('content', '').strip()
    if not content:
        return
    msg = Message(user_id=current_user.id, group_id=group_id, content=content)
    db.session.add(msg)
    db.session.commit()
    emit('receive_message', {
        'user': current_user.display_name,
        'avatar': current_user.avatar_url,
        'content': content,
        'timestamp': msg.created_at.strftime('%H:%M')
    }, room=f'group_{group_id}')

@socketio.on('join')
def on_join(data):
    join_room(f"group_{data['group_id']}")

@socketio.on('leave')
def on_leave(data):
    leave_room(f"group_{data['group_id']}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
