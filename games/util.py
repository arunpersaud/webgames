from flask import make_response
from functools import wraps, update_wrapper
from datetime import datetime
from werkzeug.http import http_date


def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers["Last-Modified"] = http_date(datetime.now())
        response.headers[
            "Cache-Control"
        ] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
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
