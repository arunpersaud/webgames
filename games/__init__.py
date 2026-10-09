"""Games to play with friends over a video call.

Configuration comes from environment variables with a FLASK_ prefix:

    FLASK_SECRET_KEY   signs the session cookie (flash messages)
    FLASK_SECRET_SEED  mixed into every card deal, so deals can't be
                       predicted from the session name alone
    FLASK_DATABASE     SQLite file for the game state
                       (default: instance/webgames.sqlite)

Both secrets are required unless the app runs in debug or testing mode.
"""

import os

from flask import Flask, render_template

from . import db
from .boggle.views import boggle
from .doko_skat.views import doko_skat
from .krazy.views import krazy
from .util import SessionNameConverter

# Everything is served from this site: no inline scripts or styles, no
# CDNs. data: images are the icons inside pico.min.css.
SECURITY_HEADERS = {
    "Content-Security-Policy": "; ".join(
        [
            "default-src 'none'",
            "script-src 'self'",
            "style-src 'self'",
            "img-src 'self' data:",
            "connect-src 'self'",
            "form-action 'self'",
            "base-uri 'none'",
            "frame-ancestors 'none'",
        ]
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DATABASE"] = os.path.join(app.instance_path, "webgames.sqlite")
    app.config.from_prefixed_env()
    if test_config:
        app.config.update(test_config)

    for key in ("SECRET_KEY", "SECRET_SEED"):
        if not app.config.get(key):
            if not (app.debug or app.testing):
                raise RuntimeError(f"FLASK_{key} is not set")
            app.config[key] = f"insecure-dev-{key.lower()}"

    db.init_app(app)
    app.url_map.converters["name"] = SessionNameConverter

    @app.after_request
    def set_security_headers(response):
        response.headers.update(SECURITY_HEADERS)
        return response

    app.register_blueprint(boggle)
    app.register_blueprint(krazy)
    app.register_blueprint(doko_skat)

    @app.route("/")
    def main():
        return render_template("index.html")

    @app.route("/favicon.ico")
    def favicon():
        return app.send_static_file("favicon.ico")

    return app
