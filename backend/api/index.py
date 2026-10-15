"""Vercel entry point: exposes the Django WSGI application as `app`."""

import sys
from pathlib import Path

# Make `config`, `catalog`, ... importable regardless of the function's working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.wsgi import application  # noqa: E402

app = application
