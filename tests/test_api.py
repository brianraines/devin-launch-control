from types import SimpleNamespace

import pytest

from launch_control.api import DevinAPI


def test_devin_api_requires_api_key(monkeypatch):
    monkeypatch.delenv("DEVIN_API_KEY", raising=False)

    with pytest.raises(RuntimeError):
        DevinAPI()


def test_post_prompt_uses_injected_session(monkeypatch):
    monkeypatch.setenv("DEVIN_API_KEY", "test-key")

    class DummySession:
        def __init__(self):
            self.calls = []

        def post(self, url, headers, json):
            self.calls.append((url, headers, json))
            return SimpleNamespace(status_code=201, text="created")

    session = DummySession()
    api = DevinAPI(session=session)

    response = api.post_prompt("Investigate outage")

    assert response.status_code == 201
    assert response.text == "created"
    assert len(session.calls) == 1

    url, headers, payload = session.calls[0]
    assert url == api.api_url
    assert headers["Authorization"] == "Bearer test-key"
    assert payload["idempotent"] is True
    assert payload["prompt"].startswith("Investigate outage")
