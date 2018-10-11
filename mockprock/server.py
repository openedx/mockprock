import atexit
import shelve
import threading
import uuid
from flask import Flask, request, jsonify
import requests


app = Flask(__name__)
app.shelf = shelve.open('/tmp/mockprock')
app.debug = True

atexit.register(app.shelf.close)

proctoring_config = {
    'download_url': 'http://host.docker.internal:11136/download',
    'name': 'MockProck',
    'config': {
        'allow_cheating': 'Allow the student to cheat',
        'allow_notes': 'Allow the student to take notes',
    },
    'instructions': [
        'First of all, have a nice day.',
        'A new window will open. You will run a system check before downloading the proctoring application.',
        'You will be asked to verify your identity as part of the proctoring exam set up. Make sure you are on a computer with a webcam, and that you have valid photo identification such as a driver\'s license or passport, before you continue.',
        'When you are finished, you will be redirected to the exam.',
        'Finally, have a nice day!'
    ]
}

@app.route('/v1/config/')
def get_config():
    return jsonify(proctoring_config)


@app.route('/v1/exam/<exam_id>/', methods=['GET'])
def get_exam(exam_id):
    exam = app.shelf.get(exam_id, {})
    return jsonify(exam)

@app.route('/v1/exam/', methods=['POST'])
def create_exam():
    exam = request.json
    exam_id = uuid.uuid4().hex
    app.shelf[exam_id] = exam
    app.logger.info('Saved exam %s from %s', exam_id, request.authorization.username)
    return jsonify({'id': exam_id})

@app.route('/v1/exam/<exam_id>/attempt/<attempt_id>/', methods=['GET', 'POST', 'PATCH'])
def exam_attempt_endpoint(exam_id, attempt_id):
    attempt = request.json
    if request.authorization:
        username = request.authorization.username
    else:
        username = None
    response = {'id': attempt_id}
    if request.method == 'POST':
        app.shelf[attempt_id] = attempt
        app.logger.info('Created attempt %s from %s %r', attempt_id, username, attempt)
    elif request.method == 'PATCH':
        app.shelf[attempt_id].update(attempt)
        status = attempt.get('status')
        if status == 'stop':
            app.logger.info('Finished attempt %s. Sending a fake review in 10 seconds...', attempt_id)
            threading.Timer(10, make_review_callback, args=[attempt_id]).start()
        else:
            app.logger.info('Changed attempt %s status to %s', attempt_id, status)
        response['status'] = status
    elif request.method == 'GET':
        download_url = '{}?attempt={}'.format(proctoring_config['download_url'], attempt_id)
        response = app.shelf.get(attempt_id, {})
        response['download_url'] = download_url
        response['instructions'] = proctoring_config['instructions']
    return jsonify(response)

@app.route('/download')
def software_download():
    attempt_id = request.args.get('attempt')
    attempt = app.shelf.get(attempt_id, {})
    app.logger.info('Requesting download for attempt %s', attempt_id)
    dl = '''
<html>
<head>
</head>
    <body><h1>Downloading...</h1>
    <p>You're pretending to download the MockProck desktop software</p>
    <p>In fact, you'll be redirected back to the exam...</p>
<script>
setTimeout(window.close, 10000);
</script>
    </body>
</html>
    '''
    threading.Timer(2, make_ready_callback, args=[attempt]).start()
    return dl

def make_ready_callback(attempt):
    try:
        callback_url = attempt['callback_url']
        token = attempt['callback_token']
        payload = {
            'token': token,
            'status': 'ready'
        }
        response = requests.post(callback_url, json=payload).json()
        app.logger.info('Got ready response from LMS: %s', response)
    except Exception:
        app.logger.exception('in ready callback')

def make_review_callback(attempt_id):
    attempt = app.shelf[attempt_id]
    callback_url = attempt['review_callback_url']
    token = attempt['callback_token']
    status = 'verified'
    comments = [
        {'comment': 'Looks suspicious', 'status': 'ok'}
    ]
    payload = {
        'token': token,
        'status': status,
        'comments': comments
    }
    response = requests.post(callback_url, json=payload).json()
    app.logger.info('Got review response from LMS: %s', response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=11136)
