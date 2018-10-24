"""
Run this server with python -m mockprock.server {client_id} {client_secret}
"""
import atexit
from pprint import pprint
import sys
import threading
import time
import uuid
from functools import wraps

import jwt
from edx_rest_api_client.client import OAuthAPIClient
from flask import Flask, abort, jsonify, request
from pickleshare import PickleShareDB

app = Flask(__name__)
app.shelf = PickleShareDB('/tmp/mockprock')
app.debug = True
app.secret_key = 'super secret'

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


def get_download_url():
    return 'http://%s/download' % request.host

def requires_token(f):
    @wraps(f)
    def _func(*args, **kwargs):
        token = request.headers.get('Authorization', ' ').split(' ')[1]
        try:
            jwt.decode(token, app.secret_key, verify=False)
        except jwt.DecodeError:
            abort(403)
        else:
            return f(*args, **kwargs)
    return _func


@app.route('/oauth2/access_token', methods=['POST'])
def access_token():
    """
    Returns a mock JWT token
    """
    grant_type = request.form['grant_type']
    client_id = request.form['client_id']
    client_secret = request.form['client_secret']
    token_type = request.form['token_type']
    assert token_type == 'jwt', 'Only JWT is supported'
    resp = {}
    if client_secret == client_id + 'secret':
        exp = 3600
        payload = {'aud': client_id, 'exp': time.time() + exp}
        token = jwt.encode(payload, app.secret_key)
        resp['access_token'] = token
        resp['expires_in'] = exp
    return jsonify(resp)

@app.route('/v1/config/')
@requires_token
def get_config():
    """
    Returns the global configuration options
    """
    proctoring_config['download_url'] = get_download_url()
    return jsonify(proctoring_config)


@app.route('/v1/exam/<exam_id>/', methods=['GET'])
@requires_token
def get_exam(exam_id):
    """
    Returns the exam
    """
    exam = app.shelf.get(exam_id, {})
    return jsonify(exam)

@app.route('/v1/exam/', methods=['POST'])
@requires_token
def create_exam():
    """
    Creates an exam, returning an external id
    """
    exam = request.json
    exam_id = uuid.uuid4().hex
    key = '%s/exam' % exam_id
    app.shelf[key] = exam
    app.logger.info('Saved exam %s from %s', exam_id, request.headers.get('Authorization'))
    pprint(exam)
    return jsonify({'id': exam_id})

@app.route('/v1/exam/<exam_id>/', methods=['POST'])
@requires_token
def update_exam(exam_id):
    """
    Updates an exam, returning the exam
    """
    exam = request.json
    key = '%s/exam' % exam_id
    if not app.shelf.get(key, None):
        app.shelf[key] = exam
        app.logger.info('Updated exam %s from %s', exam_id, request.headers.get('Authorization'))
    else:
        app.shelf[key] = exam
        app.logger.info('Got confused update request for exam %s from %s', exam_id, request.headers.get('Authorization'))
    pprint(exam)
    return jsonify({'id': exam_id})

@app.route('/v1/exam/<exam_id>/attempt/', methods=['POST'])
@requires_token
def create_attempt(exam_id):
    attempt = request.json
    attempt_id = uuid.uuid4().hex
    app.shelf['%s/%s' % (exam_id, attempt_id)] = attempt
    app.logger.info('Created attempt %s from %r', attempt_id, attempt)
    return jsonify({'id': attempt_id})

@app.route('/v1/exam/<exam_id>/attempt/<attempt_id>/', methods=['GET', 'PATCH'])
@requires_token
def exam_attempt_endpoint(exam_id, attempt_id):
    """
    Creates/retrieves/updates the exam attempt
    For convenience, the GET request also returns instructions and software download link
    for the exam
    """
    attempt = request.json
    response = {'id': attempt_id}
    key = '%s/%s' % (exam_id, attempt_id)
    if request.method == 'PATCH':
        app.shelf[key].update(attempt)
        status = attempt.get('status')
        if status == 'stop':
            app.logger.info('Finished attempt %s. Sending a fake review in 10 seconds...', attempt_id)
            threading.Timer(10, make_review_callback, args=[exam_id, attempt_id]).start()
        else:
            app.logger.info('Changed attempt %s status to %s', attempt_id, status)
        response['status'] = status
    elif request.method == 'GET':
        download_url = '{}?attempt={}&exam={}'.format(get_download_url(), attempt_id, exam_id)
        response = app.shelf.get(key, {})
        response['download_url'] = download_url
        response['instructions'] = proctoring_config['instructions']
        response['config'] = app.shelf.get('%s/exam' % exam_id, {}).get('config', {})
    return jsonify(response)

@app.route('/download')
def software_download():
    """
    Page that pretends to download software, and then calls back to edx
    to signal that the exam is ready
    """
    attempt_id = request.args.get('attempt')
    exam_id = request.args.get('exam')
    attempt = app.shelf.get('%s/%s' % (exam_id,attempt_id), {})
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
    threading.Timer(2, make_ready_callback, args=[attempt_id, attempt]).start()
    return dl

def make_ready_callback(attempt_id, attempt):
    try:
        callback_url = '%s/api/edx_proctoring/v1/proctored_exam/attempt/%s/ready' % (attempt['lms_host'], attempt_id)
        payload = {
            'status': 'ready'
        }
        response = app.client.post(callback_url, json=payload).json()
        app.logger.info('Got ready response from LMS: %s', response)
    except Exception:
        app.logger.exception('in ready callback')

def make_review_callback(exam_id, attempt_id):
    attempt = app.shelf['%s/%s' % (exam_id, attempt_id)]
    callback_url = '%s/api/edx_proctoring/v1/proctored_exam/attempt/%s/reviewed' % (attempt['lms_host'], attempt_id)
    status = 'verified'
    comments = [
        {'comment': 'Looks suspicious', 'status': 'ok'}
    ]
    payload = {
        'status': status,
        'comments': comments
    }
    response = app.client.post(callback_url, json=payload).json()
    app.logger.info('Got review response from LMS: %s', response)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='run the mockprock server',
        epilog='Retrieve the mockprock client id and secret from the LMS Django admin, and start the server with those arguments')
    parser.add_argument("client_id", type=str, help="oauth client id", nargs="?")
    parser.add_argument("client_secret", type=str, help="oauth client secret", nargs="?")
    args = parser.parse_args()

    if not (args.client_id and args.client_secret):
        parser.print_help()
        time.sleep(2)
        import webbrowser
        webbrowser.open('http://localhost:18000/admin/oauth2_provider/application/')
        sys.exit(1)
    app.client = OAuthAPIClient('http://localhost:18000', args.client_id, args.client_secret)
    app.run(host='0.0.0.0', port=11136)
