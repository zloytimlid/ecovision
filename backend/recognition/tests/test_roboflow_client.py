import base64
import logging

import pytest
import requests

from recognition.services.roboflow_client import (
    RoboflowClient,
    RoboflowError,
    RoboflowNotConfigured,
    RoboflowTimeout,
)

API_KEY = "secret-key-123"


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=None):
        self.status_code = status_code
        self._payload = payload
        self.text = text if text is not None else str(payload)

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class FakeSession:
    """Replays a list of responses/exceptions and records the requests."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.requests = []

    def post(self, url, **kwargs):
        self.requests.append({"url": url, **kwargs})
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def make_client(session, **kwargs):
    options = {
        "api_key": API_KEY,
        "api_url": "https://detect.example.com/",
        "model_id": "waste-model",
        "model_version": "3",
        "model_type": "object-detection",
        "timeout": 5,
        "min_confidence": 0.4,
        "session": session,
        **kwargs,
    }
    return RoboflowClient(**options)


def test_detection_request_format():
    session = FakeSession(FakeResponse(payload={"predictions": []}))
    result = make_client(session).predict(b"jpeg-bytes")

    assert result == {"predictions": []}
    (request,) = session.requests
    assert request["url"] == "https://detect.example.com/waste-model/3"
    assert request["params"] == {"api_key": API_KEY, "confidence": 40}
    assert request["data"] == base64.b64encode(b"jpeg-bytes")
    assert request["headers"]["Content-Type"] == "application/x-www-form-urlencoded"
    assert request["timeout"] == 5


def test_classification_request_has_no_confidence_param():
    session = FakeSession(FakeResponse(payload={"predictions": []}))
    make_client(session, model_type="classification").predict(b"x")
    assert session.requests[0]["params"] == {"api_key": API_KEY}


def test_not_configured_client_does_not_send_requests():
    session = FakeSession()
    with pytest.raises(RoboflowNotConfigured):
        make_client(session, api_key="").predict(b"x")
    assert session.requests == []


def test_retries_once_on_server_error():
    session = FakeSession(FakeResponse(503, text="busy"), FakeResponse(payload={"predictions": []}))
    assert make_client(session).predict(b"x") == {"predictions": []}
    assert len(session.requests) == 2


def test_two_server_errors_raise():
    session = FakeSession(FakeResponse(500, text="boom"), FakeResponse(502, text="boom"))
    with pytest.raises(RoboflowError):
        make_client(session).predict(b"x")
    assert len(session.requests) == 2


def test_retries_once_on_network_error():
    session = FakeSession(
        requests.ConnectionError("connection refused"),
        FakeResponse(payload={"predictions": []}),
    )
    assert make_client(session).predict(b"x") == {"predictions": []}
    assert len(session.requests) == 2


def test_client_error_is_not_retried():
    session = FakeSession(FakeResponse(403, text="Forbidden"))
    with pytest.raises(RoboflowError):
        make_client(session).predict(b"x")
    assert len(session.requests) == 1


def test_timeout_raises_timeout_error_without_retry():
    session = FakeSession(requests.ReadTimeout("read timed out"))
    with pytest.raises(RoboflowTimeout):
        make_client(session).predict(b"x")
    assert len(session.requests) == 1


@pytest.mark.parametrize(
    "response", [FakeResponse(200, payload=None, text="<html>"), FakeResponse(200, payload=[1, 2])]
)
def test_unusable_response_raises(response):
    with pytest.raises(RoboflowError):
        make_client(FakeSession(response)).predict(b"x")


def test_api_key_never_appears_in_logs_or_errors(caplog):
    caplog.set_level(logging.DEBUG)
    url_with_key = f"https://detect.example.com/waste-model/3?api_key={API_KEY}"
    session = FakeSession(
        requests.ConnectionError(f"Max retries exceeded with url: {url_with_key}"),
        FakeResponse(401, text=f"Invalid key {API_KEY}"),
    )
    with pytest.raises(RoboflowError) as exc:
        make_client(session).predict(b"x")

    assert API_KEY not in str(exc.value)
    assert exc.value.__cause__ is None
    assert caplog.records, "errors should be logged"
    assert API_KEY not in caplog.text
