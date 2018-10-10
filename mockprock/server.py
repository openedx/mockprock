import uuid
from flask import Flask, request, jsonify
import requests


app = Flask(__name__)
app.debug = True
app.exams = {}
app.attempts = {}


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
    exams = app.exams
    return jsonify(exams.get(exam_id, {}))

@app.route('/v1/exam/', methods=['POST'])
def create_exam():
    exam = request.json
    exam_id = uuid.uuid4().hex
    app.exams[exam_id] = exam
    app.logger.info('Saved exam %s from %s', exam_id, request.authorization.username)
    return jsonify({'id': exam_id})

@app.route('/v1/exam/<exam_id>/<attempt_id>/', methods=['GET', 'POST', 'PATCH'])
def exam_attempt_endpoint(exam_id, attempt_id):
    attempt = request.json
    if request.authorization:
        username = request.authorization.username
    else:
        username = None
    if request.method == 'POST':
        app.attempts[attempt_id] = attempt
        app.logger.info('Started attempt %s from %s', attempt_id, username)
    elif request.method == 'PATCH':
        app.attempts[attempt_id].update(attempt)
        if attempt.get('status') == 'stop':
            loop = asyncio.get_event_loop()
            loop.call_later(60, make_callback, attempt)
    return jsonify('ok')

@app.route('/download')
def software_download():
    app.logger.info('%s requesting download', request.authorization)
    return 'download'


def make_callback(attempt):
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
