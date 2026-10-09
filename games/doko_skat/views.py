"""
Blueprint for playing Skat and Doppelkopf online.


"""

import random
from pathlib import Path

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

from ..util import data_dir, ensure_alphanum

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


def select_game_type(game_type: str) -> tuple[Path, dict]:
    """Return game specific settings."""
    if game_type == "doko":
        db = data_dir() / "doko.db"
        game = {"title": "Doppelkopf", "link": "doko"}
    else:
        db = data_dir() / "skat.db"
        game = {"title": "Skat", "link": "skat"}
    return db, game


def tag_exists(tag: str, db: Path) -> bool:
    """Check if tag is in database.

    Assumes a file based storage/db.
    """
    if db.exists():
        with db.open("r") as f:
            for line in f:
                if line.startswith(tag):
                    return True
    return False


def add_tag(tag: str, db: Path) -> None:
    """Add a tag to the database."""
    if db.exists():
        with db.open("a") as f:
            f.write(f"{tag}\n")


@doko_skat.route("/<any(doko, skat):game_type>")
def doko(game_type="doko"):
    """Page to start a new game."""

    _, game = select_game_type(game_type)

    return render_template("doko.html", game=game)


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
    STORAGE, game = select_game_type(game_type)

    if game_type == "doko":
        players = {"A": False, "B": False, "C": False, "D": False}
    else:
        players = {"A": False, "B": False, "C": False, "skat": False}
    for player in players:
        tag = f"{seed} {player} {nr}"
        if tag_exists(tag, STORAGE):
            players[player] = True
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

    We write a tag into our database (just a text file) to see
    if the someone already requested the web page, if so we show
    an error, otherwise, we render the cards
    """
    valid_players = (
        ("A", "B", "C", "D") if game_type == "doko" else ("A", "B", "C", "skat")
    )
    if player not in valid_players:
        abort(404)

    STORAGE, game = select_game_type(game_type)

    tag = f"{seed} {player} {nr}"
    if tag_exists(tag, STORAGE):
        return render_template("doko-single-error.html", game=game)

    if game_type == "doko":
        cards = get_doko_cards(seed, nr, player)
    else:
        cards = get_skat_cards(seed, nr, player)

    suit = doko_sort_cards_by_suit(cards)
    # register page as visited
    add_tag(tag, STORAGE)

    return render_template(
        "doko-game.html",
        cards=cards,
        suit=suit,
        nr=nr,
        seed=seed,
        player=player,
        game=game,
    )
