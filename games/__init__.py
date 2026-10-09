import sys
import os

from flask import Flask, render_template
import secure

# import the different games
from .boggle.views import boggle
from .doko_skat.views import doko_skat
from .krazy.views import krazy

try:
    from .config import ProductionConfig, DevelopmentConfig
except ModuleNotFoundError:
    print("Error: please copy config_template.py to config.py")
    print("       and set the following variables:")
    print("          SECRET_KEY  (random string)")
    print("          SECRET_SEED (should be a string)")
    sys.exit()


app = Flask(__name__)
# no CSP yet: boggle loads jquery from a CDN, krazy uses an inline script
secure_headers = secure.Secure(
    xcto=secure.XContentTypeOptions(),
    xfo=secure.XFrameOptions().sameorigin(),
    referrer=secure.ReferrerPolicy().strict_origin_when_cross_origin(),
)


@app.after_request
def set_secure_headers(response):
    secure_headers.set_headers(response)
    return response


app.secret_key = os.urandom(12).hex()
if app.debug:
    app.config.from_object(DevelopmentConfig())
    print(" * Using devel config")
else:
    app.config.from_object(ProductionConfig())

# register the different games
app.register_blueprint(boggle)
app.register_blueprint(krazy)
app.register_blueprint(doko_skat)


@app.route("/")
def main():
    return render_template("index.html")
