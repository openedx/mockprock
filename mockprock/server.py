import atexit
import shelve
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
    }
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
        app.logger.info('Started attempt %s from %s %r', attempt_id, username, attempt)
    elif request.method == 'PATCH':
        app.shelf[attempt_id].update(attempt)
        if attempt.get('status') == 'stop':
            pass
            # loop = asyncio.get_event_loop()
            # loop.call_later(60, make_callback, attempt)
    elif request.method == 'GET':
        response = app.shelf.get(attempt_id, {})
        response['instructions'] = [
        '<a href="{}?attempt={}" target="_mockprock">Download the MockProck software</a>'.format(proctoring_config['download_url'], attempt_id),
        'A new window will open. You will run a system check before downloading the proctoring application.',
        'You will be asked to verify your identity as part of the proctoring exam set up. Make sure you are on a computer with a webcam, and that you have valid photo identification such as a driver\'s license or passport, before you continue.',
        'When you are finished, you will be redirected to the exam.'
    ]
    return jsonify(response)

@app.route('/download')
def software_download():
    attempt_id = request.args.get('attempt')
    attempt = app.shelf.get(attempt_id, {})
    app.logger.info('%s requesting download', request.authorization)
    dl = '''
<html>
<head>
    <meta http-equiv="refresh" content="5; url={}">
</head>
    <body><h1>Downloading</h1>
    <p>You're pretending to download the MockProck desktop software</p>
    <p>In fact, you'll be redirected back to the exam...</p>
<script>

</script>
    </body>
</html>
    '''.format(attempt.get('callback_url'))
    return dl


def make_review_callback(attempt):
    callback_url = attempt['callback_url']
    token = attempt['callback_token']
    headers = {'Authorization': 'JWT {}'.format(token)}
    status = 'verified'
    comments = []
    payload = {
        'token': token,
        'status': status,
        'comments': comments
    }
    response = requests.post(callback_url, json=payload, headers=headers).json()
    app.logger.info(response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=11136)
