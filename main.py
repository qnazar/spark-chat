from flask import Flask, request
from flask_socketio import SocketIO, join_room, emit, close_room
from models import db, User
from config import Config
from sqlalchemy.exc import SQLAlchemyError

import eventlet


eventlet.monkey_patch()
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='eventlet')

with app.app_context():
    db.create_all()


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
    return chats


@socketio.on('connection')
def connect_user():
    print('connected: ', request.sid)


@socketio.on('login')
def login_user(data):
    user = User.query.get(data['username'])

    if not user:
        try:
            user = User(username=data['username'],
                        password=data['password'],
                        session_id=request.sid,
                        is_active=True)
            db.session.add(user)
            db.session.commit()
            chats = []
            graph = build_graph()
            join_room(user.username, sid=request.sid)
            emit('registration', {'username': user.username, 'chats': chats, 'graph': graph}, to=user.username)
            emit('new node', {'username': user.username, 'is_active': user.is_active}, broadcast=True, include_self=False)
        except SQLAlchemyError as e:
            print(e)

    elif user.password == data['password']:
        user.session_id = request.sid
        user.is_active = True
        db.session.commit()
        chats = load_chats(user)
        graph = build_graph()
        join_room(user.username, sid=request.sid)
        emit('login', {'username': user.username, 'chats': chats, 'graph': graph}, to=user.username)
        emit('node active', {'username': user.username, 'is_active': user.is_active},
             broadcast=True, include_self=False)

    else:
        emit('login failed', 'wrong password')


@socketio.on('add chat')
def add_chat(data):
    user: User = User.query.get(data['current_user'])
    new_contact: User = User.query.get(data['to_user'])
    if new_contact:
        user.connects.append(new_contact)
        new_contact.connects.append(user)

        db.session.commit()
        user_chats = load_chats(user)
        contact_chats = load_chats(new_contact)

        emit('add contact', user_chats, to=user.username)
        emit('add contact', contact_chats, to=new_contact.username)

        emit('new links', [{'source': user.username, 'target': new_contact.username},
                           {'source': new_contact.username, 'target': user.username}], broadcast=True)

    else:
        emit('contact does not exist', 'contact does not exist', to=user.username)


@socketio.on('message')
def message(data):
    dest: User = User.query.get(data['to'])
    emit('message', data, to=dest.username)
    emit('msg visual', {'from': data['sender'], 'to': data['to']}, broadcast=True)


@socketio.on('disconnect')
def disconnect_user():
    user = User.query.filter_by(session_id=request.sid).first()
    if user:
        user.session_id = None
        user.is_active = False
        db.session.commit()
        close_room(user.username)
        emit('node inactive', {'username': user.username, 'is_active': False}, broadcast=True, include_self=False)


if __name__ == '__main__':
    socketio.run(app, debug=True)
