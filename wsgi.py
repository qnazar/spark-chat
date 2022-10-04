import eventlet
from eventlet import wsgi
from main import app

wsgi.server(eventlet.listen(('127.0.0.1', 5000)), app)
