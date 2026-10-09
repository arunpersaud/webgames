from datetime import datetime
from functools import update_wrapper, wraps
from pathlib import Path

from flask import current_app, make_response
from werkzeug.http import http_date


def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers["Last-Modified"] = http_date(datetime.now())
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "-1"
        return response

    return update_wrapper(no_cache, view)


def ensure_alphanum(input: str):
    input = input.lower()
    input = input.replace(" ", "")
    out = ""
    for s in input:
        if s.isalnum():
            out += s
    return out


def data_dir() -> Path:
    """Directory for game state (FLASK_DATA_DIR), created on first use."""
    path = Path(current_app.config["DATA_DIR"])
    path.mkdir(parents=True, exist_ok=True)
    return path
