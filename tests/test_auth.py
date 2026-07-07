from unittest.mock import MagicMock

from mockprock.rest_api_client.auth import SuppliedJwtAuth


def test_supplied_jwt_auth_sets_header():
    auth = SuppliedJwtAuth("my-token")
    mock_request = MagicMock()
    mock_request.headers = {}
    result = auth(mock_request)
    assert mock_request.headers["Authorization"] == "JWT my-token"
    assert result is mock_request


def test_supplied_jwt_auth_init():
    auth = SuppliedJwtAuth("test-token")
    assert auth.token == "test-token"
