import sys
import os

from flask import Flask, render_template

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


app.secret_key = os.urandom(12).hex()
if app.config["ENV"] == "development":
    app.config.from_object(DevelopmentConfig())
    print(" * Using devel config")
else:
    app.config.from_object(ProductionConfig())

app.register_blueprint(boggle)
app.register_blueprint(krazy)
app.register_blueprint(doko_skat)


@app.route("/")
def main():
    return render_template("index.html")
