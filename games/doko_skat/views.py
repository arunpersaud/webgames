from flask import Blueprint, render_template, request, redirect
from ..util import nocache
from pathlib import Path
import time
import random

doko_skat = Blueprint(
    "doko_skat",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/games/doko_skat/static",
)


@doko_skat.route("/doko")
@doko_skat.route("/doko", methods=["POST"])
@doko_skat.route("/doko/<seed>")
@doko_skat.route("/doko/<seed>/<player>")
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
