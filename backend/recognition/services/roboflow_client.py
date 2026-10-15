"""
HTTP client for the Roboflow Hosted Inference API.

The request URL carries the api_key query parameter, so neither the URL nor
the text of requests exceptions (which embeds it) is ever logged.
"""

import base64
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

DETECTION = "object-detection"
CLASSIFICATION = "classification"


class RoboflowError(Exception):
    """Roboflow is unreachable or returned an error / unusable response."""


class RoboflowTimeout(RoboflowError):
    """Roboflow did not answer within the configured timeout."""


class RoboflowNotConfigured(RoboflowError):
    """API key, model ID or model version is missing."""


class RoboflowClient:
    MAX_ATTEMPTS = 2  # one retry on 5xx or network error

    def __init__(
        self,
        api_key=None,
        api_url=None,
        model_id=None,
        model_version=None,
        model_type=None,
        timeout=None,
        min_confidence=None,
        session=None,
    ):
        self.api_key = api_key if api_key is not None else settings.ROBOFLOW_API_KEY
        self.api_url = (api_url or settings.ROBOFLOW_API_URL).rstrip("/")
        self.model_id = model_id if model_id is not None else settings.ROBOFLOW_MODEL_ID
        self.model_version = (
            model_version if model_version is not None else settings.ROBOFLOW_MODEL_VERSION
        )
        self.model_type = model_type or settings.ROBOFLOW_MODEL_TYPE
        self.timeout = timeout if timeout is not None else settings.ROBOFLOW_TIMEOUT_SECONDS
        self.min_confidence = (
            min_confidence if min_confidence is not None else settings.ROBOFLOW_MIN_CONFIDENCE
        )
        self.session = session or requests.Session()

    @property
    def is_configured(self):
        return bool(self.api_key and self.model_id and self.model_version)

    def predict(self, image_bytes):
        """Send a JPEG/PNG image to the model and return the parsed JSON response."""
        if not self.is_configured:
            logger.error(
                "Roboflow is not configured: set ROBOFLOW_API_KEY, ROBOFLOW_MODEL_ID "
                "and ROBOFLOW_MODEL_VERSION in backend/.env"
            )
            raise RoboflowNotConfigured("Roboflow API key, model ID or version is not set")

        url = f"{self.api_url}/{self.model_id}/{self.model_version}"
        params = {"api_key": self.api_key}
        if self.model_type == DETECTION:
            params["confidence"] = round(self.min_confidence * 100)
        body = base64.b64encode(image_bytes)

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            is_last = attempt == self.MAX_ATTEMPTS
            try:
                response = self.session.post(
                    url,
                    params=params,
                    data=body,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=self.timeout,
                )
            except requests.Timeout:
                # Not retried: a second attempt would double the wait for the user.
                logger.error("Roboflow timeout after %ss (model %s)", self.timeout, self.model_id)
                raise RoboflowTimeout("Roboflow request timed out") from None
            except requests.RequestException as exc:
                logger.warning(
                    "Roboflow network error %s (attempt %d/%d)",
                    type(exc).__name__,
                    attempt,
                    self.MAX_ATTEMPTS,
                )
                if is_last:
                    raise RoboflowError(f"Network error: {type(exc).__name__}") from None
                continue

            if response.status_code >= 500 and not is_last:
                logger.warning(
                    "Roboflow returned HTTP %d (attempt %d/%d)",
                    response.status_code,
                    attempt,
                    self.MAX_ATTEMPTS,
                )
                continue

            if not response.ok:
                logger.error(
                    "Roboflow returned HTTP %d: %s",
                    response.status_code,
                    response.text[:300].replace(self.api_key, "***"),
                )
                raise RoboflowError(f"HTTP {response.status_code}")

            try:
                data = response.json()
            except ValueError:
                logger.error("Roboflow returned a non-JSON response")
                raise RoboflowError("Invalid JSON in response") from None
            if not isinstance(data, dict):
                logger.error("Roboflow returned unexpected JSON: %s", type(data).__name__)
                raise RoboflowError("Unexpected response format")
            return data

        raise RoboflowError("No response")  # unreachable, keeps linters happy
