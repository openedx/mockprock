"""
These endpoints emulate a desktop proctoring application
They support starting a session, stopping a session, and pinging for availability
"""
from flask import Blueprint, jsonify
import time

fake_application = Blueprint(__name__, 'mockprock')

# this assumes there's only one application "running". haha
fake_application.desktop_status = None


@fake_application.after_request
def allow_crossorigin_requests(response):
    """
    Since these are ajax requests, we need to allow cross site access
    """
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Cache-Control'] = 'no-cache'
    return response


@fake_application.route('/desktop/ping')
def ping():
    return jsonify({'status': fake_application.desktop_status})


@fake_application.route('/desktop/start', methods=['POST'])
def start():
    fake_application.desktop_status = 'running'
    return jsonify({'status': fake_application.desktop_status})


@fake_application.route('/desktop/stop', methods=['POST'])
def stop():
    fake_application.desktop_status = 'uploading'
    time.sleep(60)
    return jsonify({'status': fake_application.desktop_status})

