"""
Module pulled out of edx-rest-api-client for use interacting with the edX api from a non-django context
"""
import datetime

import requests
import requests.utils

from mockprock.rest_api_client.auth import SuppliedJwtAuth

def user_agent():
    """
    Return a User-Agent that identifies this client.
    """
    client_name = 'mockprock'
    return "{} edx-rest-api-client/{} {}".format(
        requests.utils.default_user_agent(),  # e.g. "python-requests/2.9.1"
        "1.9.2",  # version of this client
        client_name
    )

USER_AGENT = user_agent()

def get_oauth_access_token(url, client_id, client_secret, token_type='jwt', grant_type='client_credentials',
                           refresh_token=None):
    """ Retrieves OAuth 2.0 access token using the given grant type.

    Args:
        url (str): Oauth2 access token endpoint
        client_id (str): client ID
        client_secret (str): client secret
    Kwargs:
        token_type (str): Type of token to return. Options include bearer and jwt.
        grant_type (str): One of 'client_credentials' or 'refresh_token'
        refresh_token (str): The previous access token (for grant_type=refresh_token)

    Returns:
        tuple: Tuple containing access token string and expiration datetime.
    """
    now = datetime.datetime.utcnow()
    data = {
        'grant_type': grant_type,
        'client_id': client_id,
        'client_secret': client_secret,
        'token_type': token_type,
    }
    if refresh_token:
        data['refresh_token'] = refresh_token
    else:
        assert grant_type != 'refresh_token', "refresh_token parameter required"

    response = requests.post(
        url,
        data=data,
        headers={
            'User-Agent': USER_AGENT,
        },
    )

    data = response.json()
    try:
        access_token = data['access_token']
        expires_in = data['expires_in']
    except KeyError:
        raise requests.RequestException(response=response)

    expires_at = now + datetime.timedelta(seconds=expires_in)

    return access_token, expires_at

class OAuthAPIClient(requests.Session):
    """
    A :class:`requests.Session` that automatically authenticates against edX's preferred
    authentication method, given a client id and client secret. The underlying implementation
    is subject to change.
    """
    oauth_uri = '/oauth2/access_token'

    def __init__(self, base_url, client_id, client_secret, **kwargs):
        """
        Args:
            base_url (str): base url of LMS instance
            client_id (str): Client ID
            client_secret (str): Client secret
        """
        super(OAuthAPIClient, self).__init__(**kwargs)
        self.headers['user-agent'] = USER_AGENT
        self._base_url = base_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._expiration = datetime.datetime(1983, 4, 6, 7, 30, 0)
        self.auth = SuppliedJwtAuth(None)

    def _check_auth(self):
        if datetime.datetime.utcnow() > self._expiration:
            url = self._base_url + self.oauth_uri
            grant_type = 'client_credentials'
            self.auth.token, self._expiration = get_oauth_access_token(
                url,
                self._client_id,
                self._client_secret,
                grant_type=grant_type)

    def request(self, method, url, **kwargs):  # pylint: disable=arguments-differ
        """
        Overrides Session.request to ensure that the session is authenticated
        """
        self._check_auth()
        return super(OAuthAPIClient, self).request(method, url, **kwargs)
