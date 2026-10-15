"""Settings for the test suite. Tests never talk to the real Roboflow API."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")

from .settings import *  # noqa: E402,F403

ROBOFLOW_API_KEY = "test-api-key"
ROBOFLOW_API_URL = "https://roboflow.invalid"
ROBOFLOW_MODEL_ID = "test-model"
ROBOFLOW_MODEL_VERSION = "1"
ROBOFLOW_MODEL_TYPE = "object-detection"
ROBOFLOW_TIMEOUT_SECONDS = 1.0
ROBOFLOW_MIN_CONFIDENCE = 0.40
LOW_CONFIDENCE_THRESHOLD = 0.60

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
