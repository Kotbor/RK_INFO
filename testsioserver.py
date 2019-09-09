import eventlet
import socketio

sio = socketio.Server()
app = socketio.WSGIApp(sio, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})

@sio.event
def connect(sid, environ):
    print('connect ', sid)

@sio.event
def my_message(sid, data):
    print('message ', data)

@sio.event
def disconnect(sid):
    print('disconnect ', sid)

@sio.event
def posOrder(sid,data):
    print('Received pos order:%s'% data)
    sio.emit('responseOrder',data=data)

@sio.event
def authentication(sid,data):
    sio.emit('authenticated', data={})


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)