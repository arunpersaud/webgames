"""
Blueprint for playing Skat and Doppelkopf online.


"""

import random
from pathlib import Path
from typing import List, Optional

from flask import Blueprint, render_template, request, redirect, current_app

doko_skat = Blueprint(
    "doko_skat",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/games/doko_skat/static",
)


def shuffle_cards(seed: str, nr: int, number_of_cards: int) -> List[int]:
    """Return a shuffled list of cards.

    The cards are just integer number between 0, 1,..., number_of_cards-1.

    The seed is set so that during a game the same set of randomized
    cards are used.

    """
    random.seed(seed + str(nr) + current_app.config["SECRET_SEED"])
    cards = list(range(number_of_cards))
    random.shuffle(cards)
    return cards


def get_doko_cards(seed: str, nr: int, player: str) -> List[str]:
    """For a given seed and player, return the players list of cards as png files."""
    cards = shuffle_cards(48)
    # pick the card for the player
    if player == "A":
        cards = cards[:12]
    elif player == "B":
        cards = cards[12:24]
    elif player == "C":
        cards = cards[24:36]
    elif player == "D":
        cards = cards[36:]
    # normalize to just the odd numbers, since we don't have duplicate png files
    cards = [2 * (c // 2) + 1 for c in cards]
    # the png files are sorted in the corrrect way, e.g. 0 is the ten of hearts, etc.
    cards = sorted(cards)
    cards = ["doko/{}.png".format(c) for c in cards]
    return cards


def get_skat_cards(seed: str, nr: int, player: str) -> List[str]:
    """For a given seed and player, return the players list of cards as png files."""
    cards = shuffle_cards(32)
    if player == "A":
        cards = cards[:10]
    elif player == "B":
        cards = cards[10:20]
    elif player == "C":
        cards = cards[20:30]
    elif player == "skat":
        cards = cards[30:]
    # the png files are sorted in the corrrect way, e.g. 0 is the ten of hearts, etc.
    cards = sorted(cards)
    cards = ["skat/{}.png".format(c) for c in cards]
    return cards


@doko_skat.route("/<game_type>")
@doko_skat.route("/<game_type>", methods=["POST"])
@doko_skat.route("/<game_type>/<seed>/<nr>/")
@doko_skat.route("/<game_type>/<seed>/<nr>/<player>")
def doko(
    game_type="doko",
    seed: Optional[str] = None,
    player: Optional[str] = None,
    nr: int = 1,
):
    nr = int(nr)

    if game_type == "doko":
        STORAGE = Path("tmp") / "doko.db"
        game = {"title": "Doppelkopf", "link": "doko"}
    else:
        STORAGE = Path("tmp") / "skat.db"
        game = {"title": "Skat", "link": "skat"}

    if player is not None:
        # handle request from player to see cards

        # we write a tag into our database (just a text file) to see
        # if the someone already requested the web page, if so we show
        # an error, otherwise, we render the cards
        tag = f"{seed} {player} {nr}"
        # check if page has already been visited
        if STORAGE.exists():
            with STORAGE.open("r") as f:
                for l in f:
                    if l.startswith(tag):
                        return render_template("doko-single-error.html", game=game)

        # get cards
        if game_type == "doko":
            cards = get_doko_cards(seed, nr, player)
        else:
            cards = get_skat_cards(seed, nr, player)

        # register page as visited
        with STORAGE.open("a") as f:
            f.write("{}\n".format(tag))
        return render_template(
            "doko-game.html", cards=cards, nr=nr, seed=seed, player=player, game=game
        )

    if request.method == "POST":
        # someone entered a new seesion name, do some error checking
        # on the seed and redirect to the first game
        seed = request.form["name"].lower()
        seed = seed.replace(" ", "")
        out = ""
        for s in seed:
            if s.isalnum():
                out += s
        seed = out
        return redirect(f"/{game_type}/{seed}/{nr}")

    if seed is not None:
        # show a page for the current game to see how already looked
        # at their hand and who hasn't
        if game_type == "doko":
            players = {"A": False, "B": False, "C": False, "D": False}
        else:
            players = {"A": False, "B": False, "C": False, "skat": False}
        for player in players:
            tag = f"{seed} {player} {nr}"
            if STORAGE.exists():
                with STORAGE.open("r") as f:
                    for l in f:
                        if l.startswith(tag):
                            players[player] = True
        return render_template(
            "doko-start.html", seed=seed, nr=nr, players=players, game=game
        )

    # none of the above, show form to create a new session.
    return render_template("doko.html", game=game)
