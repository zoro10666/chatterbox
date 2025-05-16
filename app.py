from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, emit
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
socketio = SocketIO(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Routes
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['username'] = username
            return redirect(url_for('home'))
        flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    users = [u.username for u in User.query.all()]
    return render_template('home.html', users=users)

@app.route('/chat/<username>')
def private_chat(username):
    if 'username' not in session or username == session['username']:
        return redirect(url_for('home'))
    users = [u.username for u in User.query.all()]
    if username not in users:
        flash('User does not exist.')
        return redirect(url_for('home'))
    room = '_'.join(sorted([session['username'], username]))
    return render_template('private_chat.html', friend=username, room=room)

# SocketIO Events
@socketio.on('join_room')
def handle_join_room(data):
    join_room(data['room'])

@socketio.on('send_message')
def handle_send_message(data):
    emit('receive_message', {
        'msg': data['msg'],
        'username': data['username']
    }, room=data['room'], include_self=False)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)

