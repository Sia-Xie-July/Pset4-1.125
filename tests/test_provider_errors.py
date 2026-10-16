"""FICTIONAL error responses never expose environment credentials."""
import json

import requests

from lib.model_provider import request_error


def test_schema_errors_are_actionable_but_credentials_are_withheld(monkeypatch):
    key = 'FICTIONAL_PRIVATE_VALUE_FOR_THIS_TEST'
    monkeypatch.setenv('MODEL_API_KEY', key)
    response = requests.Response()
    response.status_code = 400
    response._content = json.dumps({'error': {'message': 'Invalid schema: unsupported keyword'}}).encode()
    assert 'unsupported keyword' in request_error(requests.HTTPError(response=response))
    response._content = json.dumps({'error': {'message': key}}).encode()
    assert key not in request_error(requests.HTTPError(response=response))
    response.status_code = 401
    response._content = json.dumps({'error': {'message': 'Incorrect key: FICTIONAL-fragment'}}).encode()
    assert 'fragment' not in request_error(requests.HTTPError(response=response))
