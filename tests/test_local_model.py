"""Local transport tests; synthetic inputs are not collected evidence."""
import json
from types import SimpleNamespace

import pytest

from lib.model_provider import ask
from lib.stage_runtime import InvalidInput


def invoke(tmp_path, monkeypatch, payload=None):
    monkeypatch.setenv('MODEL_PROVIDER', 'ollama_local')
    monkeypatch.setenv('MODEL_NAME', 'qwen3:8b')
    monkeypatch.setenv('INVOCATION_ID', 'local-transport-test')
    metrics = {'models': [], 'model_calls': []}
    result = ask('smoke', tmp_path, {'mode': 'example'}, 'Synthetic test only.',
                 'Return status ok.', payload or {'example': True},
                 {'type': 'object', 'properties': {'status': {'type': 'string'}},
                  'required': ['status'], 'additionalProperties': False}, metrics)
    return result, metrics


def test_local_no_auth_or_proxy(tmp_path, monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'FICTIONAL_UNUSED_SECRET')
    class Session:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, url, **kwargs):
            assert self.trust_env is False
            assert url == 'http://127.0.0.1:11434/api/chat'
            assert 'headers' not in kwargs
            assert kwargs['json']['think'] is False
            return SimpleNamespace(raise_for_status=lambda: None, text=json.dumps({
                'message': {'content': '{"status":"ok"}'}, 'done': True,
                'done_reason': 'stop', 'prompt_eval_count': 20, 'eval_count': 5}))
    monkeypatch.setattr('lib.model_provider.requests.Session', Session)
    result, metrics = invoke(tmp_path, monkeypatch)
    assert result == {'status': 'ok'}
    assert metrics['cost_usd'] == 0
    invoke(tmp_path, monkeypatch)
    assert len(list((tmp_path / 'prompts/rendered').glob('*.json'))) == 2
    assert len(list((tmp_path / 'model_outputs').glob('*.txt'))) == 2


def test_local_context_preflight(tmp_path, monkeypatch):
    with pytest.raises(InvalidInput, match='no request sent'):
        invoke(tmp_path, monkeypatch, {'example': 'x' * 40000})


def test_local_reject_remote(tmp_path, monkeypatch):
    monkeypatch.setenv('LOCAL_MODEL_BASE_URL', 'https://example.com')
    with pytest.raises(InvalidInput, match='loopback'):
        invoke(tmp_path, monkeypatch)
