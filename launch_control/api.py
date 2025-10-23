"""
API implementation for the devin launch control.
"""

import json
import os
import urllib.error
import urllib.request
import uuid
from typing import Mapping, Optional

try:
    import requests  # type: ignore
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]


class DevinAPI:
    """
    API implementation for the devin launch control.
    """

    # Devin AI API details
    API_URL = "https://api.devin.ai/v1/sessions"
    API_KEY_ENV_VAR = "DEVIN_API_KEY"

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        session=None,
    ):
        self.api_url = api_url or self.API_URL
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.getenv(self.API_KEY_ENV_VAR)
        if not self.api_key:
            raise RuntimeError(
                f"{self.API_KEY_ENV_VAR} environment variable is required."
            )

        if session is not None:
            self._session = session
        elif requests is not None:
            self._session = requests
        else:
            self._session = None

    def _post_json(self, data: Mapping) -> "_HttpResponse":
        """
        Post JSON to the API.
        """

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if self._session is not None:
            try:
                response = self._session.post(self.api_url, headers=headers, json=data)
                return _HttpResponse(response.status_code, response.text)
            except Exception as exc:  # pragma: no cover - depends on session impl
                return _HttpResponse(0, str(exc))

        payload = json.dumps(data).encode("utf-8")
        request = urllib.request.Request(
            self.api_url,
            data=payload,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request) as resp:
                body = resp.read().decode("utf-8")
                status_code = resp.getcode()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            status_code = exc.code
        except urllib.error.URLError as exc:
            return _HttpResponse(0, str(exc.reason))

        return _HttpResponse(status_code, body)

    def post_prompt(self, prompt: str):
        """
        Post a session to the API.
        """

        # add a UUID to the end of the prompt to make it unique
        prompt = f"{prompt}\n\n{uuid.uuid4()}"

        data = {"prompt": f"{prompt}", "idempotent": True}

        return self._post_json(data)


class _HttpResponse:
    """Minimal response object to mimic requests.Response."""

    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text

    def json(self):
        return json.loads(self.text or "{}")
