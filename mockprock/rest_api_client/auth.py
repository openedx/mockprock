"""
Auth code ripped out of edx-rest-api-client for use here
"""
from requests.auth import AuthBase


class SuppliedJwtAuth(AuthBase):
    """Attaches a supplied JWT to the given Request object."""

    def __init__(self, token):
        """Instantiate the auth class."""
        self.token = token

    def __call__(self, r):
        """Update the request headers."""
        r.headers['Authorization'] = 'JWT {jwt}'.format(jwt=self.token)
        return r

