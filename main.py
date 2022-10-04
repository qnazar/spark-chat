from flask import Flask, request
from flask_socketio import SocketIO, join_room
from models import db, User
from config import Config
from flask_session import Session

import eventlet


eventlet.monkey_patch()
app = Flask(__name__)
app.config.from_object(Config)
app.config['SESSION_TYPE'] = 'filesystem'

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

with app.app_context():
    db.create_all()
    print('db created tables')


users = {}


def build_graph():
    users = User.query.all()
    graph = {
        'nodes': [],
        'links': []
    }
    for user in users:
        entry = {'username': user.username, 'is_active': user.is_active}
        graph['nodes'].append(entry)
        for contact in user.connects:
            entry = {'source': user.username, 'target': contact.username}
            graph['links'].append(entry)
    return graph


def load_chats(user: User):
    chats = [u.username for u in user.connects]
    print(chats)
    return chats


@socketio.on('connection')
def connect_user(message):
    users[request.sid] = None
    print('connected')


@socketio.on('disconnect')
def disconnect_user():
    print('disconnected')
    user = users.pop(request.sid)
    user = User.query.get(user)
    if user:
        user.is_active = False
        db.session.commit()
        graph = build_graph()
        socketio.emit('logout', {'graph': graph})


@socketio.on('login')
def login_user(data):
    user = User.query.filter_by(username=data['username']).first()
    if not user:
        user = User(username=data['username'],
                    password=data['password'],
                    is_active=True)
        db.session.add(user)
        chats = []
    elif user.password == data['password']:
        user.is_active = True
        chats = load_chats(user)
    else:
        socketio.emit('login failed', 'wrong password')
        return
    users[request.sid] = user.username
    db.session.commit()
    join_room(user.username, sid=request.sid)

    graph = build_graph()
    socketio.emit('login success', {'username': user.username, 'chats': chats, 'graph': graph}, room=user.username)
    socketio.emit('graph', {'graph': graph, 'from': 'login'}, broadcast=True)


@socketio.on('add chat')
def add_chat(data):
    current_user: User = User.query.get(data['current_user'])
    new_contact: User = User.query.get(data['to_user'])
    if new_contact:
        current_user.connects.append(new_contact)
        db.session.commit()
        chats = load_chats(current_user)

        graph = build_graph()
        socketio.emit('new connection added', {'username': current_user.username, 'chats': chats}, room=current_user.username)
        socketio.emit('graph', {'graph': graph, 'from': 'add_chat'}, broadcast=True)
    else:
        socketio.emit('no such user', 'no such user')


@socketio.on('message')
def message(data):
    dest: User = User.query.get(data['to'])
    socketio.emit('message', data, room=dest.username)


if __name__ == '__main__':
    socketio.run(app, debug=True)
