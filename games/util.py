from datetime import datetime
from functools import update_wrapper, wraps

from flask import make_response
from werkzeug.http import http_date
from werkzeug.routing import BaseConverter


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


def ensure_alphanum(text: str) -> str:
    """Lowercase letters and digits of text; used for session names and words."""
    return "".join(c for c in text.lower() if c.isalnum())


class SessionNameConverter(BaseConverter):
    """URL part <name:seed>: a session name made by ensure_alphanum()."""

    regex = r"[^\W_]+"
