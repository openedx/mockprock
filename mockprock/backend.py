from edx_proctoring.backends.rest import BaseRestProctoringProvider

class MockProckBackend(BaseRestProctoringProvider):
    base_url = 'http://localhost:11136'
    human_readable_name = u'Mock Proctoring Service'

