import sys, os

INTERP = "/home/arun/bin/python3.8"

# INTERP is present twice so that the new python interpreter knows the actual executable path
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

from flask import Flask, render_template
import time
import random
from pathlib import Path

application = Flask(__name__)


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
        ["a", "a", "a", "f", "r", "s"],
        ["a", "a", "e", "e", "e", "e"],
        ["a", "a", "f", "i", "r", "s"],
        ["a", "d", "e", "n", "n", "n"],
        ["a", "e", "e", "e", "e", "m"],
        ["a", "e", "e", "g", "m", "u"],
        ["a", "e", "g", "m", "n", "n"],
        ["a", "f", "i", "r", "s", "y"],
        ["b", "j", "k", "qu", "x", "z"],
        ["c", "c", "e", "n", "s", "t"],
        ["c", "e", "i", "i", "l", "t"],
        ["c", "e", "i", "l", "p", "t"],
        ["c", "e", "i", "p", "s", "t"],
        ["d", "d", "h", "n", "o", "t"],
        ["d", "h", "h", "l", "o", "r"],
        ["d", "h", "l", "n", "o", "r"],
        ["d", "h", "l", "n", "o", "r"],
        ["e", "i", "i", "i", "t", "t"],
        ["e", "m", "o", "t", "t", "t"],
        ["e", "n", "s", "s", "s", "u"],
        ["f", "i", "p", "r", "s", "y"],
        ["g", "o", "r", "r", "v", "w"],
        ["i", "p", "r", "r", "r", "y"],
        ["n", "o", "o", "t", "u", "w"],
        ["o", "o", "o", "t", "t", "u"],
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
    else:
        now = time.time()
        last = FILE.stat().st_mtime
        if now - last > 30:
            boggle_text = gen_func()
            with FILE.open("w") as f:
                f.write(boggle_text)
        else:
            with FILE.open("r") as f:
                boggle_text = f.read()
    boggle_text = boggle_text.split(",")
    return boggle_text


@application.route("/boggle")
def boggle_4x4():
    boggle_text = load_boggle(generate_4x4, "4x4.txt")
    return render_template("boggle.html", seconds=30, boggle=boggle_text, size=4)


@application.route("/big_boggle")
def boggle_5x5():
    boggle_text = load_boggle(generate_5x5, "5x5.txt")
    return render_template("boggle.html", seconds=30, boggle=boggle_text, size=5)


@application.route("/doko")
def doko():
    return render_template("doko.html")


if __name__ == "__main__":
    application.run(debug=True)
