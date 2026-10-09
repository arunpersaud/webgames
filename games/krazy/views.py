import json
import random
import sqlite3
import time
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

from .. import db
from ..util import ensure_alphanum, nocache

krazy = Blueprint(
    "krazy",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/games/krazy/static",
)


RESOURCES = Path(__file__).parent / "resource"
LANGUAGES = ["de"]
MAX_PLAYERS = 7


def load_round(seed: str, nr: int) -> dict:
    row = (
        db.get_db()
        .execute("SELECT data FROM krazy_round WHERE seed = ? AND nr = ?", (seed, nr))
        .fetchone()
    )
    if row is None:
        abort(404)
    return json.loads(row["data"])


def load_game_data(seed: str, nr: int):
    data = load_round(seed, nr)
    return data["words"], len(data["player-info"]), data["language"]


def load_player_data(seed: str, nr: int, player: int):
    data = load_round(seed, nr)
    if not 0 <= player < len(data["player-info"]):
        abort(404)
    player_data = data["player-info"][player]
    return player_data["letters"], player_data["word"]


def load_plays(seed: str, nr: int) -> dict[int, sqlite3.Row]:
    """Words and guesses of all players in a round, by player number."""
    rows = db.get_db().execute(
        "SELECT player, word, guess FROM krazy_play WHERE seed = ? AND nr = ?",
        (seed, nr),
    )
    return {row["player"]: row for row in rows}


def save_play(seed: str, nr: int, player: int, column: str, value: str) -> None:
    assert column in ("word", "guess")
    db.get_db().execute(
        f"""INSERT INTO krazy_play (seed, nr, player, {column}, updated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT DO UPDATE SET {column} = excluded.{column},
                                      updated = excluded.updated""",
        (seed, nr, player, value, time.time()),
    )


def get_list_of_created_words(seed: str, nr: int):
    """Get a list of all created words.

    return '-' if player has not created a word yet
    always returns an array of length MAX_PLAYERS
    """
    plays = load_plays(seed, nr)
    return [
        plays[i]["word"] if i in plays and plays[i]["word"] is not None else "-"
        for i in range(MAX_PLAYERS)
    ]


def draw_letters(pool: list[str], n: int, rng: random.Random) -> list[str]:
    """n random letters from pool, using several copies of pool if it is too small."""
    copies = -(-n // len(pool))
    return rng.sample(pool * copies, n)


def create_new_game(language, seed, nr, nr_players):
    rng = random.Random(seed + str(nr) + current_app.config["SECRET_SEED"])

    # load possible letters and words and shuffle
    input_file = RESOURCES / f"{language}.txt"
    with input_file.open() as f:
        data = json.load(f)
        vowels = draw_letters(data["vowels"], 3 * nr_players, rng)
        consonants = draw_letters(data["consonants"], 6 * nr_players, rng)
        words = rng.sample(data["words"], len(data["words"]))

    # create session file that stores the data for each player and a
    # list of all words in play
    out = {}
    player_info = []
    for i in range(nr_players):
        tmp = {}
        tmp["letters"] = vowels[3 * i : 3 * (i + 1)] + consonants[6 * i : 6 * (i + 1)]
        tmp["word"] = words[i]
        player_info.append(tmp)
    out["player-info"] = player_info
    words = words[:6] if nr_players <= 5 else words[: nr_players + 1]
    # shuffle again, since at the moment the words are ordered by player
    words = rng.sample(words, len(words))
    out["words"] = words
    out["language"] = language

    # IGNORE: when several players finish at once, the first one creates
    # the next round
    db.get_db().execute(
        "INSERT OR IGNORE INTO krazy_round VALUES (?, ?, ?, ?)",
        (seed, nr, json.dumps(out), time.time()),
    )


@krazy.route("/krazy")
def krazy_start():
    """The webpage to start a game.

    One user selects the language, the number of players, and a name
    for the session.

    """
    return render_template("krazy-start.html")


@krazy.route("/krazy", methods=["POST"])
def create_krazy_game():
    """Handle the request to start a game.

    It creates a text file that stores the words for the round and the
    distribution of letters for each user.

    """

    nr = 1

    seed = ensure_alphanum(request.form.get("name", ""))
    nr_players = request.form.get("players", type=int)
    language = request.form.get("language")
    if nr_players is None or not 1 <= nr_players <= MAX_PLAYERS:
        abort(400)
    if language not in LANGUAGES:
        abort(400)
    if not seed:
        flash("Please enter a session name")
        return redirect(url_for("krazy.krazy_start"))

    # a new game with an old name starts from scratch
    db.cleanup()
    conn = db.get_db()
    conn.execute("DELETE FROM krazy_round WHERE seed = ?", (seed,))
    conn.execute("DELETE FROM krazy_play WHERE seed = ?", (seed,))
    create_new_game(language, seed, nr, nr_players)

    return render_template(
        "krazy-init-players.html",
        seed=seed,
        nr=nr,
        players=list(range(nr_players)),
        root=request.url_root,
    )


@krazy.route("/krazy/<name:seed>/<int:nr>")
def krazy_start_round(seed, nr):
    words, nr_players, _ = load_game_data(seed, nr)
    return render_template(
        "krazy-init-players.html",
        seed=seed,
        nr=nr,
        players=list(range(nr_players)),
        root=request.url_root,
    )


@krazy.route("/krazy/<name:seed>/<int:nr>/<int:player>")
def krazy_play(seed, nr, player):
    """Handle the play for a single player

    If the user hasn't created a word, display that webpage, otherwise
    show the user the list of created words

    """
    words, nr_players, _ = load_game_data(seed, nr)
    letters, word = load_player_data(seed, nr, player)

    # user hasn't created a word
    if get_list_of_created_words(seed, nr)[player] == "-":
        return render_template(
            "krazy-create_word.html", seed=seed, nr=nr, letters=letters, word=word
        )

    # user already created their word
    created_words = get_list_of_created_words(seed, nr)[:nr_players]

    return render_template(
        "krazy-guess_word.html",
        seed=seed,
        myword=word,
        words=words,
        created_words=created_words,
        player=player,
    )


@krazy.route("/krazy/<name:seed>/<int:nr>/<int:player>", methods=["POST"])
def krazy_play_submit(seed, nr, player):
    """Handle response from user play."""
    words, nr_players, _ = load_game_data(seed, nr)

    # handle if user created a word
    if "myword" in request.form:
        myword = ensure_alphanum(request.form["myword"])

        # ensure that the correct letters are used
        letters, word = load_player_data(seed, nr, player)
        for letter in myword:
            if letter in letters:
                letters.remove(letter)
            else:
                flash(
                    f"Letter -{letter}- not in your list of letters"
                    " (or not often enough)"
                )
                return redirect(
                    url_for("krazy.krazy_play", seed=seed, nr=nr, player=player)
                )

        save_play(seed, nr, player, "word", myword)

        return redirect(url_for("krazy.krazy_play", seed=seed, nr=nr, player=player))

    # handle user guess: for each created word, the number of the word it fits
    tmp = []
    for i in range(1, nr_players + 1):
        g = request.form.get(f"player-{player}-{i}", type=int)
        if g is not None and 1 <= g <= len(words):
            tmp.append(g)

    if len(tmp) != nr_players:
        flash("You need to assign a guess for each word")
        return redirect(url_for("krazy.krazy_play", seed=seed, nr=nr, player=player))

    if len(set(tmp)) != len(tmp):
        flash("You cannot use the same number twice")
        return redirect(url_for("krazy.krazy_play", seed=seed, nr=nr, player=player))

    save_play(seed, nr, player, "guess", json.dumps(tmp))

    return redirect(url_for("krazy.krazy_final", seed=seed, nr=nr, player=player))


def guess_version(seed: str, nr: int) -> str:
    """Changes whenever a player submits a guess."""
    plays = load_plays(seed, nr)
    return ",".join(str(p) for p in sorted(plays) if plays[p]["guess"] is not None)


@krazy.route("/krazy/<name:seed>/<int:nr>/status")
@nocache
def round_status(seed, nr):
    """Polled by the results page, to reload when a new guess comes in."""
    load_round(seed, nr)  # 404 for unknown rounds
    return {"version": guess_version(seed, nr)}


@krazy.route("/krazy/<name:seed>/<int:nr>/<int:player>/final")
def krazy_final(seed, nr, player):
    """Show all guesses from all players."""
    words, nr_players, language = load_game_data(seed, nr)

    # get ready for next round
    create_new_game(language, seed, nr + 1, nr_players)

    created_words = get_list_of_created_words(seed, nr)
    player_name = [f"{w} (player{i})" for i, w in enumerate(created_words)]

    plays = load_plays(seed, nr)
    guesses = []
    for i in range(nr_players):
        if i in plays and plays[i]["guess"] is not None:
            guess_words = ["-"] * (len(words) + 1)
            for j, g in enumerate(json.loads(plays[i]["guess"])):
                guess_words[g] = created_words[j]
            guess_words[0] = player_name[i]
            guesses.append(guess_words)

    return render_template(
        "krazy-final.html",
        seed=seed,
        nr=nr,
        words=words,
        player=player,
        player_name=player_name,
        guesses=guesses,
        version=guess_version(seed, nr),
    )
