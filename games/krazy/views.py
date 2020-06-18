from flask import Blueprint, render_template, request, redirect, abort, flash
from ..util import nocache, ensure_alphanum
from pathlib import Path
import time
import random
import json

krazy = Blueprint(
    "krazy",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/games/krazy/static",
)


LANGUAGES = ["de"]
MAX_PLAYERS = 7


def make_tmpdir():
    """Ensure tmp directory exists"""
    tmpdir = Path("tmp")
    tmpdir.mkdir(parents=True, exist_ok=True)
    return tmpdir


def load_game_data(seed: str):
    tmpdir = make_tmpdir()
    datafile = tmpdir / f"{seed}.json"

    if not datafile.exists():
        abort(404)

    with datafile.open("r") as f:
        data = json.load(f)

    words = data[-1]
    nr_players = len(data) - 1
    return words, nr_players


def load_player_data(seed: str, player: int):
    tmpdir = make_tmpdir()
    datafile = tmpdir / f"{seed}.json"

    if not datafile.exists():
        abort(404)

    with datafile.open("r") as f:
        data = json.load(f)

    player_data = data[player]
    letters = player_data["letters"]
    word = data[-1][player]

    return letters, word


def get_list_of_created_words(seed):
    """Get a list of all created words.

    return '-' if player has not created a word yet
    always returns an array of length MAX_PLAYERS
    """
    tmpdir = make_tmpdir()

    created_words = []
    for i in range(MAX_PLAYERS):
        player_file = tmpdir / f"{seed}-player{i}.txt"
        if player_file.exists():
            with player_file.open("r") as f:
                myword = f.read()
            created_words.append(myword)
        else:
            created_words.append("-")
    return created_words


@krazy.route("/krazy")
def krazy_start():
    """The webage to start a game.

    One user selects the langugae, the number of players, and a name
    for the session.

    """
    return render_template("krazy-start.html")


@krazy.route("/krazy", methods=["POST"])
def create_krazy_game():
    """Handle the request to start a game.

    It creates a text file that stores the words for the round and the
    distribution of letters for each user.

    """
    tmpdir = make_tmpdir()

    seed = ensure_alphanum(request.form["name"])
    nr_players = int(request.form["players"])

    random.seed(seed)

    language = request.form["language"]
    if language not in LANGUAGES:
        flash(f"Language {language} not supported")
        return redirect(f"/krazy")

    # clean up old round
    for i in range(MAX_PLAYERS):
        player_file = tmpdir / f"{seed}-player{i}.txt"
        player_guess_file = tmpdir / f"{seed}-player{i}-guess.txt"
        for f in [player_file, player_guess_file]:
            if f.exists():
                f.unlink()

    # load possible letters and words and shuffle
    input_file = Path(f"games/krazy/resource/{language}.txt")
    with input_file.open() as f:
        data = json.load(f)
        vocals = random.sample(data["vocals"] * 50, len(data["vocals"] * 50))
        consonants = random.sample(
            data["consonants"] * 50, len(data["consonants"] * 50)
        )
        words = random.sample(data["words"], len(data["words"]))

    # create session file that stores the data for each player and a
    # list of all words in play
    out = []
    for i in range(nr_players):
        tmp = {}
        tmp["letters"] = vocals[3 * i : 3 * (i + 1)] + consonants[6 * i : 6 * (i + 1)]
        out.append(tmp)
    if nr_players <= 5:
        out.append(words[:6])
    else:
        out.append(words[: nr_players + 1])

    with (tmpdir / f"{seed}.json").open("w") as f:
        json.dump(out, f)

    return render_template(
        "krazy-init-players.html", seed=seed, players=list(range(nr_players))
    )


@krazy.route("/krazy/<seed>/<player>")
def krazy_play(seed, player):
    """Handle the play for a single player

    If the user hasn't created a word, display that webpage, otherwise
    show the user the list of created words

    """
    tmpdir = make_tmpdir()

    player = int(player)
    seed = ensure_alphanum(seed)

    words, nr_players = load_game_data(seed)
    letters, word = load_player_data(seed, player)

    # user hasn't created a word
    if not (tmpdir / f"{seed}-player{player}.txt").exists():
        return render_template(
            "krazy-create_word.html", seed=seed, letters="-".join(letters), word=word
        )

    # user already created their word
    created_words = get_list_of_created_words(seed)[:nr_players]

    return render_template(
        "krazy-guess_word.html",
        seed=seed,
        words=words,
        created_words=created_words,
        player=player,
    )


@krazy.route("/krazy/<seed>/<player>", methods=["POST"])
def krazy_play_submit(seed, player):
    """Handle response from user play."""
    tmpdir = make_tmpdir()

    player = int(player)
    seed = ensure_alphanum(seed)

    words, nr_players = load_game_data(seed)

    # handle if user created a word
    if "myword" in request.form:
        myword = ensure_alphanum(request.form["myword"])

        # ensure that the correct letters are used
        letters, word = load_player_data(seed, player)
        for l in myword:
            if l in letters:
                letters.remove(l)
            else:
                flash(f"Letter -{l}- not in your list of letters (or not often enough)")
                return redirect(f"/krazy/{seed}/{player}")

        with (tmpdir / f"{seed}-player{player}.txt").open("w") as f:
            f.write(myword)

        return redirect(f"/krazy/{seed}/{player}")

    # handle user guess
    tmp = []
    for i in range(nr_players):
        for j in range(len(words)):
            if f"player-{i}-{j}" in request.form:
                # convert to int for user validation
                g = int(request.form[f"player-{i}-{j}"])
                # we do need strings for writing to file later
                tmp.append(str(g))

    if len(tmp) != nr_players:
        flash("You need to assigne a guess for each word")
        return redirect(f"/krazy/{seed}/{player}")

    if len(set(tmp)) != len(tmp):
        flash("You can use the same number twice")
        return redirect(f"/krazy/{seed}/{player}")

    with (tmpdir / f"{seed}-player{player}-guess.txt").open("w") as f:
        f.write(",".join(tmp))

    return redirect(f"/krazy/{seed}/final")


@krazy.route("/krazy/<seed>/final")
def krazy_final(seed):
    """Show all guesses from all players."""
    tmpdir = make_tmpdir()

    seed = ensure_alphanum(seed)
    words, nr_players = load_game_data(seed)

    created_words = get_list_of_created_words(seed)
    player = [f"{w} (player{i})" for i, w in enumerate(created_words)]

    guesses = []
    for i in range(nr_players):
        player_guess_file = tmpdir / f"{seed}-player{i}-guess.txt"
        if player_guess_file.exists():
            with player_guess_file.open("r") as f:
                guess = [int(i) for i in f.read().split(",")]
                guess_words = ["-"] * (len(words) + 1)
                for j, g in enumerate(guess):
                    guess_words[g] = created_words[j]
                guess_words[0] = player[i]
                guesses.append(guess_words)

    return render_template(
        "krazy-final.html", seed=seed, words=words, player=player, guesses=guesses
    )