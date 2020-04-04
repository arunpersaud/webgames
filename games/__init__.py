from flask import Flask, render_template

from .boggle.views import boggle
from .doko_skat.views import doko_skat


app = Flask(__name__)
app.register_blueprint(boggle)
app.register_blueprint(doko_skat)


@app.route("/")
def main():
    return render_template("index.html")


