"""
Blueprint for playing Skat and Doppelkopf online.


"""

import random
from pathlib import Path

from flask import Blueprint, render_template, request, redirect, current_app

doko_skat = Blueprint(
    "doko_skat",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/games/doko_skat/static",
)


def get_doko_cards(seed, nr, player):
    """For a given seed and player, return a list of png files for the
    cards.

    """
    random.seed(seed + str(nr) + current_app.config["SECRET_SEED"])
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
    return cards


def get_skat_cards(seed, nr, player):
    """For a given seed and player, return a list of png files for the
    cards.

    """
    random.seed(seed + str(nr) + current_app.config["SECRET_SEED"])
    cards = list(range(32))
    random.shuffle(cards)
    if player == "A":
        cards = cards[:10]
    elif player == "B":
        cards = cards[10:20]
    elif player == "C":
        cards = cards[20:30]
    elif player == "skat":
        cards = cards[30:]
    # normalize to just the odd numbers
    cards = sorted(cards)
    cards = ["skat/{}.png".format(c) for c in cards]
    return cards


@doko_skat.route("/<game_type>")
@doko_skat.route("/<game_type>", methods=["POST"])
@doko_skat.route("/<game_type>/<seed>/<nr>/")
@doko_skat.route("/<game_type>/<seed>/<nr>/<player>")
def doko(game_type="doko", seed=None, player=None, nr=1):
    nr = int(nr)

    SKAT = {"title": "Skat", "link": "skat"}
    DOKO = {"title": "Doppelkopf", "link": "doko"}

    if game_type == "doko":
        game = DOKO
        FILE = Path("tmp") / "doko.db"
    else:
        FILE = Path("tmp") / "skat.db"
        game = SKAT

    if player is not None:
        tag = f"{seed} {player} {nr}"
        if FILE.exists():
            with FILE.open("r") as f:
                for l in f:
                    if l.startswith(tag):
                        return render_template("doko-single-error.html", game=game)

        if game_type == "doko":
            cards = get_doko_cards(seed, nr, player)
        else:
            cards = get_skat_cards(seed, nr, player)

        with FILE.open("a") as f:
            f.write("{}\n".format(tag))
        return render_template(
            "doko-game.html", cards=cards, nr=nr, seed=seed, player=player, game=game
        )

    if request.method == "POST":
        seed = request.form["name"].lower()
        seed = seed.replace(" ", "")
        out = ""
        for s in seed:
            if s.isalnum():
                out += s
        seed = out
        return redirect(f"/{game_type}/{seed}/{nr}")

    if seed is not None:
        if game_type == "doko":
            players = {"A": False, "B": False, "C": False, "D": False}
        else:
            players = {"A": False, "B": False, "C": False, "skat": False}
        for player in players:
            tag = f"{seed} {player} {nr}"
            if FILE.exists():
                with FILE.open("r") as f:
                    for l in f:
                        if l.startswith(tag):
                            players[player] = True
        return render_template(
            "doko-start.html", seed=seed, nr=nr, players=players, game=game
        )

    return render_template("doko.html", game=game)
