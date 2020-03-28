import sys, os

INTERP = "/home/arun/bin/python3.8"

# INTERP is present twice so that the new python interpreter knows the actual executable path
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

from flask import Flask, render_template, request, redirect
import time
import random
from pathlib import Path

application = Flask(__name__)

BOGGLE_TIME = 5 * 60

from flask import make_response
from functools import wraps, update_wrapper
from datetime import datetime
from werkzeug.http import http_date

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = http_date(datetime.now())
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)


@application.route("/")
def main():
    return render_template("index.html")


def generate_4x4():
    letters = [
        ["A", "E", "A", "N", "E", "G"],
        ["W", "N", "G", "E", "E", "H"],
        ["A", "H", "S", "P", "C", "O"],
        ["L", "N", "H", "N", "R", "Z"],
        ["A", "S", "P", "F", "F", "K"],
        ["T", "S", "T", "I", "Y", "D"],
        ["O", "B", "J", "O", "A", "B"],
        ["O", "W", "T", "O", "A", "T"],
        ["I", "O", "T", "M", "U", "C"],
        ["E", "R", "T", "T", "Y", "L"],
        ["R", "Y", "V", "D", "E", "L"],
        ["T", "O", "E", "S", "S", "I"],
        ["L", "R", "E", "I", "X", "D"],
        ["T", "E", "R", "W", "H", "V"],
        ["E", "I", "U", "N", "E", "S"],
        ["N", "U", "I", "H", "M", "Qu"],
    ]
    random.shuffle(letters)
    boggle_text = ",".join([random.choice(l) for l in letters])
    return boggle_text


def generate_5x5():
    letters = [
        ["A", "A", "A", "F", "R", "S"],
        ["A", "A", "E", "E", "E", "E"],
        ["A", "A", "F", "I", "R", "S"],
        ["A", "D", "E", "N", "N", "N"],
        ["A", "E", "E", "E", "E", "M"],
        ["A", "E", "E", "G", "M", "U"],
        ["A", "E", "G", "M", "N", "N"],
        ["A", "F", "I", "R", "S", "Y"],
        ["B", "J", "K", "Qu", "X", "Z"],
        ["C", "C", "E", "N", "S", "T"],
        ["C", "E", "I", "I", "L", "T"],
        ["C", "E", "I", "L", "P", "T"],
        ["C", "E", "I", "P", "S", "T"],
        ["D", "D", "H", "N", "O", "T"],
        ["D", "H", "H", "L", "O", "R"],
        ["D", "H", "L", "N", "O", "R"],
        ["D", "H", "L", "N", "O", "R"],
        ["E", "I", "I", "I", "T", "T"],
        ["E", "M", "O", "T", "T", "T"],
        ["E", "N", "S", "S", "S", "U"],
        ["F", "I", "P", "R", "S", "Y"],
        ["G", "O", "R", "R", "V", "W"],
        ["I", "P", "R", "R", "R", "Y"],
        ["N", "O", "O", "T", "U", "W"],
        ["O", "O", "O", "T", "T", "U"],
    ]
    random.shuffle(letters)
    boggle_text = ",".join([random.choice(l) for l in letters])
    return boggle_text


def boggle_cleanup_tmp():
    DIR = Path("tmp")
    now = time.time()
    for f in DIR.glob("*?x?.txt"):
        t = int(f.stat().st_mtime)
        # delete everything older than 1h
        if now - t > 60 * 60:
            f.unlink()


def generate_boggle_file(gen_func, filename):
    boggle_cleanup_tmp()
    FILE = Path("tmp") / filename
    boggle_text = gen_func()
    with FILE.open("w") as f:
        f.write(boggle_text)


def load_boggle(filename):
    FILE = Path("tmp") / filename
    if not FILE.exists():
        return "" , 0
    with FILE.open("r") as f:
        boggle_text = f.read()
    boggle_text = boggle_text.split(",")
    t = int(FILE.stat().st_mtime)
    return boggle_text, t


@application.route("/boggle/<size>/<seed>/start")
@nocache
def start_boggle(size, seed):
    if size == "4x4":
        generate_boggle_file(generate_4x4, "{}-{}.txt".format(seed, size))
    else:
        generate_boggle_file(generate_5x5, "{}-{}.txt".format(seed, size))
    return "{started: 1}"


@application.route("/boggle/<size>/<seed>/update")
@nocache
def create_boggle(size, seed):
    FILE = Path("tmp") / "{}-{}.txt".format(seed, size)
    if not FILE.exists():
        return "{-2}"

    last = int(FILE.stat().st_mtime)
    return str(last)


@application.route("/boggle", methods=["POST"])
def create_boggle_game():
    seed = request.form["name"].lower()
    seed = seed.replace(" ", "")
    out = ""
    for s in seed:
        if s.isalnum():
            out += s
    seed = out

    size = int(request.form["size"])

    if size == 4:
        generate_boggle_file(generate_4x4, "{}-4x4.txt".format(seed))
        return redirect("/boggle/4x4/{}".format(seed))
    elif size == 5:
        generate_boggle_file(generate_5x5, "{}-5x5.txt".format(seed))
        return redirect("/boggle/5x5/{}".format(seed))


@application.route("/boggle/<size>/<seed>")
@application.route("/boggle")
def boggle_4x4(seed=None, size="4x4"):

    if seed is not None:
        if size == "4x4":
            s = 4
        else:
            s = 5

        boggle_text, t = load_boggle("{}-{}.txt".format(seed, size))
        return render_template(
            "boggle.html", boggle=boggle_text, fileage=t, size=s, seed=seed
        )

    return render_template("boggle-start.html", seed=seed)


@application.route("/doko")
@application.route("/doko", methods=["POST"])
@application.route("/doko/<seed>")
@application.route("/doko/<seed>/<player>")
def doko(seed=None, player=None):

    if player is not None:
        tag = "{} {}".format(seed, player)
        FILE = Path("tmp") / "doko.db"
        if FILE.exists():
            with FILE.open("r") as f:
                for l in f:
                    if l.startswith(tag):
                        return render_template("doko-single-error.html")
        random.seed(seed)
        cards = list(range(48))
        random.shuffle(cards)
        if player == "A":
            cards = cards[:12]
        elif player == "B":
            cards = cards[12:24]
        elif player == "C":
            cards = cards[24:36]
        elif player == "D":
            cards = cards[36:]
        # normalize to just the odd numbers
        cards = [2 * (c // 2) + 1 for c in cards]
        cards = sorted(cards)
        cards = ["doko/{}.png".format(c) for c in cards]
        with FILE.open("a") as f:
            f.write("{}\n".format(tag))
        return render_template("doko-game.html", cards=cards)

    if request.method == "POST":
        seed = request.form["name"].lower()
        seed = seed.replace(" ", "")
        out = ""
        for s in seed:
            if s.isalnum():
                out += s
        seed = out

    if seed is not None:
        return render_template("doko-start.html", seed=seed)

    return render_template("doko.html")


if __name__ == "__main__":
    application.run(debug=True)
