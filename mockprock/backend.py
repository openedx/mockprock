"""
To enable this backend, configure your LMS and CMS settings like this:
PROCTORING_BACKENDS = {
    'DEFAULT': 'mockprock',
    'mockprock': {
        'client_id': 'abcd',
        'client_secret': 'secret'
    }
}
"""

from edx_proctoring.backends.rest import BaseRestProctoringProvider


class MockProckBackend(BaseRestProctoringProvider):
    base_url = u'http://host.docker.internal:11136'
    verbose_name = u'Mock Proctoring Service'
    needs_oauth = True
    token_expiration_time = 86400
