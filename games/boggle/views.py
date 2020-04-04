from flask import Blueprint, render_template, request, redirect
from ..util import nocache
from pathlib import Path
import time
import random

boggle = Blueprint(
    "boggle",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/games/boggle/static",
)

BOGGLE_TIME = 5 * 60


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
        return "", 0
    with FILE.open("r") as f:
        boggle_text = f.read()
    boggle_text = boggle_text.split(",")
    t = int(FILE.stat().st_mtime)
    return boggle_text, t


@boggle.route("/boggle/<size>/<seed>/start")
@nocache
def start_boggle(size, seed):
    if size == "4x4":
        generate_boggle_file(generate_4x4, "{}-{}.txt".format(seed, size))
    else:
        generate_boggle_file(generate_5x5, "{}-{}.txt".format(seed, size))
    return "{started: 1}"


@boggle.route("/boggle/<size>/<seed>/update")
@nocache
def create_boggle(size, seed):
    FILE = Path("tmp") / "{}-{}.txt".format(seed, size)
    if not FILE.exists():
        return "{-2}"

    last = int(FILE.stat().st_mtime)
    return str(last)


@boggle.route("/boggle", methods=["POST"])
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


@boggle.route("/boggle/<size>/<seed>")
@boggle.route("/boggle")
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
