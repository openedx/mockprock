"""
Run this server with python -m mockprock.server {client_id} {client_secret}
"""
import atexit
import sys
import threading
import time
from collections import Iterable
from functools import wraps
from pprint import pprint

import jwt
from flask import Flask, abort, jsonify, render_template, request

from edx_rest_api_client.client import OAuthAPIClient
from mockprock.db import init_app
from mockprock.desktop_views import fake_application


app = Flask(__name__)
app.debug = True
app.secret_key = 'super secret'
init_app(app)

app.register_blueprint(fake_application)

proctoring_config = {
    'download_url': 'http://host.docker.internal:11136/download',
    'name': 'MockProck',
    'rules': {
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
    return u'http://%s/download' % request.host


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
        resp[u'access_token'] = token.decode('utf8')
        resp[u'expires_in'] = exp
    return jsonify(resp)


@app.route('/api/v1/config/')
@requires_token
def get_config():
    """
    Returns the global configuration options
    """
    proctoring_config[u'download_url'] = get_download_url()
    return jsonify(proctoring_config)


@app.route('/api/v1/exam/<exam_id>/', methods=['GET'])
@requires_token
def get_exam(exam_id):
    """
    Returns the exam
    """
    exam = app.db.get_exam(exam_id) or {}
    return jsonify(exam)


@app.route('/api/v1/exam/', methods=['POST'])
@requires_token
def create_exam():
    """
    Creates an exam, returning an external id
    """
    exam = request.json
    exam_id = app.db.save_exam(exam, request.headers.get('Authorization'))
    pprint(exam)
    return jsonify({u'id': exam_id})


@app.route('/api/v1/exam/<exam_id>/', methods=['POST'])
@requires_token
def update_exam(exam_id):
    """
    Updates an exam, returning the exam
    """
    exam = request.json
    exam['external_id'] = exam_id
    app.db.save_exam(exam, request.headers.get('Authorization'))
    pprint(exam)
    return jsonify({u'id': exam_id})


@app.route('/api/v1/exam/<exam_id>/attempt/', methods=['POST'])
@requires_token
def create_attempt(exam_id):
    attempt = request.json
    attempt['exam_id'] = exam_id
    app.db.save_attempt(attempt)
    attempt_id = attempt['id']
    return jsonify({u'id': attempt_id})


@app.route('/api/v1/exam/<exam_id>/attempt/<attempt_id>/', methods=['GET', 'PATCH'])
@requires_token
def exam_attempt_endpoint(exam_id, attempt_id):
    """
    Creates/retrieves/updates the exam attempt
    For convenience, the GET request also returns instructions and software download link
    for the exam
    """
    attempt = request.json
    response = {'id': attempt_id}
    dbattempt = app.db.get_attempt(exam_id, attempt_id)
    if request.method == 'PATCH':
        dbattempt.update(attempt)
        app.db.save_attempt(dbattempt)
        status = attempt.get('status')
        if status == 'submitted':
            app.logger.info('Finished attempt %s. Sending a fake review in 10 seconds...', attempt_id)
            threading.Timer(10, make_review_callback, args=[exam_id, attempt_id]).start()
        else:
            app.logger.info('Changed attempt %s status to %s', attempt_id, status)
        response['status'] = status
    elif request.method == 'GET':
        download_url = u'{}?attempt={}&exam={}'.format(get_download_url(), attempt_id, exam_id)
        response = dbattempt
        response[u'download_url'] = download_url
        response[u'instructions'] = proctoring_config['instructions']
        response[u'rules'] = app.db.get_exam(exam_id).get('rules', {})
    return jsonify(response)


class CourseIdIterator(Iterable):
    def __init__(self, client_id):
        self.client_id = client_id

    def __iter__(self):
        for exam in app.db.get_exams():
            yield exam['course_id']


@app.route('/api/v1/instructor/<client_id>/')
def instructor_dashboard(client_id):
    secret = client_id + 'secret'
    token = request.args.get('jwt')
    if not token:
        abort(403, 'JWT token required')
    decoded = jwt.decode(token, secret, issuer=client_id, course_id=CourseIdIterator(client_id))
    course_id = decoded['course_id']
    exams = []
    for exam_id in decoded.get('exam', []):
        exam = app.db.get_exam(exam_id)
        exams.append(exam)

    for exam in app.db.get_exams():
        if exam['course_id'] == course_id:
            exams.append(exam)

    context = {
        'client_id': client_id,
        'token': decoded,
        'course_id': course_id,
        'exams': exams,
        'attempt_ids': decoded.get('attempt', []),
    }
    return render_template('dashboard.html', **context)


@app.route('/download')
def software_download():
    """
    Page that pretends to download software, and then calls back to edx
    to signal that the exam is ready
    """
    attempt_id = request.args.get('attempt')
    exam_id = request.args.get('exam')
    attempt = app.db.get_attempt(exam_id, attempt_id)
    app.logger.info('Requesting download for attempt %s', attempt_id)
    threading.Timer(2, make_ready_callback, args=[attempt_id, attempt]).start()
    return render_template('download.html', attempt_id=attempt_id, exam_id=exam_id)


def make_ready_callback(attempt_id, attempt):
    try:
        callback_url = u'%s/api/edx_proctoring/v1/proctored_exam/attempt/%s/ready' % (attempt['lms_host'], attempt_id)
        payload = {
            u'status': u'ready'
        }
        app.logger.info('Calling back to %s', callback_url)
        response = app.client.post(callback_url, json=payload).json()
        app.logger.info('Got ready response from LMS: %s', response)
    except Exception as ex:
        app.logger.exception('in ready callback')
        if hasattr(ex, 'response'):
            app.logger.info('LMS error response: %r', ex.response.content)


def make_review_callback(exam_id, attempt_id):
    try:
        attempt = app.db.get_attempt(exam_id, attempt_id)
        callback_url = '%s/api/edx_proctoring/v1/proctored_exam/attempt/%s/reviewed' % (attempt['lms_host'], attempt_id)
        status = u'passed'
        comments = [
            {u'comment': u'Looks suspicious', u'status': u'ok'}
        ]
        payload = {
            u'status': status,
            u'comments': comments
        }
        app.logger.info('Calling back to %s', callback_url)
        response = app.client.post(callback_url, json=payload).json()
    except Exception as ex:
        app.logger.exception('in review callback')
        if hasattr(ex, 'response'):
            app.logger.info('LMS error response: %r', ex.response.content)
    else:
        app.logger.info('Got review response from LMS: %s', response)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='run the mockprock server',
        epilog='Retrieve the mockprock client id and secret from the LMS Django admin, and start the server with those arguments')
    parser.add_argument("client_id", type=str, help="oauth client id", nargs="?")
    parser.add_argument("client_secret", type=str, help="oauth client secret", nargs="?")
    parser.add_argument('-l', dest='lms_host', type=str, help='LMS host', default='http://host.docker.internal:18000')
    args = parser.parse_args()

    if not (args.client_id and args.client_secret):
        parser.print_help()
        time.sleep(2)
        import webbrowser
        webbrowser.open('%s/admin/oauth2_provider/application/' % args.lms_host)
        sys.exit(1)
    app.client = OAuthAPIClient(args.lms_host, args.client_id, args.client_secret)
    app.run(host='0.0.0.0', port=11136)
