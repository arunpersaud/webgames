"""
Blueprint for playing Skat and Doppelkopf online.


"""

import random
import time

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from .. import db
from ..util import ensure_alphanum

doko_skat = Blueprint(
    "doko_skat",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/games/doko_skat/static",
)


def shuffle_cards(seed: str, nr: int, number_of_cards: int) -> list[int]:
    """Return a shuffled list of cards.

    The cards are just integer number between 0, 1,..., number_of_cards-1.

    The seed is set so that during a game the same set of randomized
    cards are used.

    """
    rng = random.Random(seed + str(nr) + current_app.config["SECRET_SEED"])
    cards = list(range(number_of_cards))
    rng.shuffle(cards)
    return cards


def get_doko_cards(seed: str, nr: int, player: str) -> list[str]:
    """For a given seed and player, return the players list of cards as png files."""
    cards = shuffle_cards(seed, nr, 48)
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
    # the png files are sorted in the correct way, e.g. 0 is the ten of hearts, etc.
    cards = sorted(cards)
    cards = [f"doko/{c}.png" for c in cards]
    return cards


def get_skat_cards(seed: str, nr: int, player: str) -> list[str]:
    """For a given seed and player, return the players list of cards as png files."""
    cards = shuffle_cards(seed, nr, 32)
    if player == "A":
        cards = cards[:10]
    elif player == "B":
        cards = cards[10:20]
    elif player == "C":
        cards = cards[20:30]
    elif player == "skat":
        cards = cards[30:]
    # the png files are sorted in the correct way, e.g. 0 is the ten of hearts, etc.
    cards = sorted(cards)
    cards = [f"skat/{c}.png" for c in cards]
    return cards


def doko_sort_cards_by_suit(cards: list[str]) -> tuple[list[str]]:
    clubs = [3, 11, 27, 29, 31, 33]
    spades = [5, 13, 35, 37, 39, 41]
    hearts = [1, 7, 15, 43, 45, 47]
    diamonds = [9, 17, 19, 21, 23, 25]

    clubs = [f"doko/{n}.png" for n in clubs]
    spades = [f"doko/{n}.png" for n in spades]
    hearts = [f"doko/{n}.png" for n in hearts]
    diamonds = [f"doko/{n}.png" for n in diamonds]

    my_clubs = [c for c in cards if c in clubs]
    my_spades = [c for c in cards if c in spades]
    my_hearts = [c for c in cards if c in hearts]
    my_diamonds = [c for c in cards if c in diamonds]

    return my_clubs, my_spades, my_hearts, my_diamonds


GAMES = {
    "doko": {"title": "Doppelkopf", "link": "doko", "players": ("A", "B", "C", "D")},
    "skat": {"title": "Skat", "link": "skat", "players": ("A", "B", "C", "skat")},
}


def seen_hands(game: str, seed: str, nr: int) -> set[str]:
    """Players whose hand was already shown in this game."""
    rows = db.get_db().execute(
        "SELECT player FROM hand_seen WHERE game = ? AND seed = ? AND nr = ?",
        (game, seed, nr),
    )
    return {row["player"] for row in rows}


def mark_seen(game: str, seed: str, nr: int, player: str) -> bool:
    """Record that a hand is shown; False if it was shown before.

    One statement, so two people opening the same hand at the same time
    can't both see it.
    """
    cursor = db.get_db().execute(
        "INSERT OR IGNORE INTO hand_seen VALUES (?, ?, ?, ?, ?)",
        (game, seed, nr, player, time.time()),
    )
    return cursor.rowcount == 1


@doko_skat.route("/<any(doko, skat):game_type>")
def doko(game_type="doko"):
    """Page to start a new game."""

    return render_template("doko.html", game=GAMES[game_type])


@doko_skat.route("/<any(doko, skat):game_type>/<name:seed>/<int:nr>/")
def display_game(
    game_type="doko",
    seed: str = None,
    nr: int = 1,
):
    """Game overview page.

    Show a page for the current game to see who already looked
    at their hand and who hasn't
    """
    game = GAMES[game_type]
    seen = seen_hands(game_type, seed, nr)
    players = {player: player in seen for player in game["players"]}
    return render_template(
        "doko-start.html", seed=seed, nr=nr, players=players, game=game
    )


@doko_skat.route("/<any(doko, skat):game_type>", methods=["POST"])
def start_game(
    game_type="doko",
):
    """Someone entered a new session name.

    Do some error checking on the seed and redirect to the first game
    """
    seed = ensure_alphanum(request.form.get("name", ""))
    if not seed:
        flash("Please enter a session name")
        return redirect(url_for("doko_skat.doko", game_type=game_type))
    db.cleanup()
    return redirect(
        url_for("doko_skat.display_game", game_type=game_type, seed=seed, nr=1)
    )


@doko_skat.route("/<any(doko, skat):game_type>/<name:seed>/<int:nr>/<player>")
def display_cards(
    game_type="doko",
    seed: str = None,
    player: str = None,
    nr: int = 1,
):
    """Handle request from player to see cards.

    Each hand is shown only once: the first request is recorded in the
    database, later requests get an error page.
    """
    game = GAMES[game_type]
    if player not in game["players"]:
        abort(404)

    if not mark_seen(game_type, seed, nr, player):
        return render_template("doko-single-error.html", game=game)

    if game_type == "doko":
        cards = get_doko_cards(seed, nr, player)
    else:
        cards = get_skat_cards(seed, nr, player)

    suit = doko_sort_cards_by_suit(cards)

    return render_template(
        "doko-game.html",
        cards=cards,
        suit=suit,
        nr=nr,
        seed=seed,
        player=player,
        game=game,
    )
