import sys, os

INTERP = "/home/arun/bin/python3.8"

# INTERP is present twice so that the new python interpreter knows the actual executable path
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

from flask import Flask, render_template, request
import time
import random
from pathlib import Path

application = Flask(__name__)

BOGGLE_TIME = 5 * 60


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


def load_boggle(gen_func, filename):
    FILE = Path("tmp") / filename
    if not FILE.exists():
        boggle_text = gen_func()
        with FILE.open("w") as f:
            f.write(boggle_text)
        dt = 0
    else:
        now = time.time()
        last = FILE.stat().st_mtime
        dt = now - last
        if now - last > BOGGLE_TIME:
            boggle_text = gen_func()
            with FILE.open("w") as f:
                f.write(boggle_text)
            dt = 0
        else:
            with FILE.open("r") as f:
                boggle_text = f.read()
    boggle_text = boggle_text.split(",")
    return boggle_text, dt


@application.route("/boggle")
def boggle_4x4():
    boggle_text, dt = load_boggle(generate_4x4, "4x4.txt")
    return render_template(
        "boggle.html", seconds=int(BOGGLE_TIME - dt), boggle=boggle_text, size=4
    )


@application.route("/big_boggle")
def boggle_5x5():
    boggle_text, dt = load_boggle(generate_5x5, "5x5.txt")
    return render_template(
        "boggle.html", seconds=int(BOGGLE_TIME - dt), boggle=boggle_text, size=5
    )


@application.route("/doko")
@application.route("/doko", methods=["POST"])
@application.route("/doko/<seed>")
@application.route("/doko/<seed>/<player>")
def doko(seed=None, player=None):

    if player is not None:
        tag = "{} {}".format(seed, player)
        FILE = Path("tmp") / "doko.db"
        if FILE.exists():
            with FILE.open('r') as f:
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
        cards = [2*(c//2)+1 for c in cards]
        cards = sorted(cards)
        cards = ["doko/{}.png".format(c) for c in cards]
        with FILE.open('a') as f:
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
