import random
import sqlite3
import time

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from .. import db
from ..util import ensure_alphanum, nocache

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
    boggle_text = ",".join([random.choice(die) for die in letters])
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
    boggle_text = ",".join([random.choice(die) for die in letters])
    return boggle_text


def new_board(seed: str, size: str) -> None:
    """Roll the dice for a new board (replaces an existing one)."""
    letters = generate_4x4() if size == "4x4" else generate_5x5()
    db.cleanup()
    # started must grow, so that every open page notices the new board
    db.get_db().execute(
        """INSERT INTO boggle VALUES (?, ?, ?, ?)
           ON CONFLICT DO UPDATE SET letters = excluded.letters,
               started = max(excluded.started, boggle.started + 1)""",
        (seed, size, letters, time.time_ns() // 1_000_000),
    )


def load_board(seed: str, size: str) -> sqlite3.Row:
    """The current board; anyone with the link gets one if it doesn't exist."""
    query = "SELECT letters, started FROM boggle WHERE seed = ? AND size = ?"
    row = db.get_db().execute(query, (seed, size)).fetchone()
    if row is None:
        new_board(seed, size)
        row = db.get_db().execute(query, (seed, size)).fetchone()
    return row


@boggle.route("/boggle/<any(4x4, 5x5):size>/<name:seed>/start")
@nocache
def start_boggle(size, seed):
    new_board(seed, size)
    return "{started: 1}"


@boggle.route("/boggle/<any(4x4, 5x5):size>/<name:seed>/update")
@nocache
def create_boggle(size, seed):
    row = (
        db.get_db()
        .execute("SELECT started FROM boggle WHERE seed = ? AND size = ?", (seed, size))
        .fetchone()
    )
    if row is None:
        return "{-2}"
    return str(row["started"])


@boggle.route("/boggle", methods=["POST"])
def create_boggle_game():
    seed = ensure_alphanum(request.form.get("name", ""))
    size = request.form.get("size", type=int)
    if size not in (4, 5):
        abort(400)
    if not seed:
        flash("Please enter a name for the game")
        return redirect(url_for("boggle.boggle_4x4"))

    size = f"{size}x{size}"
    new_board(seed, size)
    return redirect(url_for("boggle.boggle_4x4", size=size, seed=seed))


@boggle.route("/boggle/<any(4x4, 5x5):size>/<name:seed>")
@boggle.route("/boggle")
def boggle_4x4(seed=None, size="4x4"):
    if seed is not None:
        s = 4 if size == "4x4" else 5
        board = load_board(seed, size)
        return render_template(
            "boggle.html",
            boggle=board["letters"].split(","),
            fileage=board["started"],
            size=s,
            seed=seed,
        )

    return render_template("boggle-start.html", seed=seed)
