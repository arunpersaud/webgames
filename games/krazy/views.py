import json
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


def load_game_data(seed: str, nr: int):
    tmpdir = data_dir()
    datafile = tmpdir / f"{seed}-{nr}.json"

    if not datafile.exists():
        abort(404)

    with datafile.open("r") as f:
        data = json.load(f)

    words = data["words"]
    nr_players = len(data["player-info"])
    language = data["language"]
    return words, nr_players, language


def load_player_data(seed: str, nr: int, player: int):
    tmpdir = data_dir()
    datafile = tmpdir / f"{seed}-{nr}.json"

    if not datafile.exists():
        abort(404)

    with datafile.open("r") as f:
        data = json.load(f)

    if not 0 <= player < len(data["player-info"]):
        abort(404)
    player_data = data["player-info"][player]
    letters = player_data["letters"]
    word = player_data["word"]

    return letters, word


def get_list_of_created_words(seed: str, nr: int):
    """Get a list of all created words.

    return '-' if player has not created a word yet
    always returns an array of length MAX_PLAYERS
    """
    tmpdir = data_dir()

    created_words = []
    for i in range(MAX_PLAYERS):
        player_file = tmpdir / f"{seed}-{nr}-player{i}.txt"
        if player_file.exists():
            with player_file.open("r") as f:
                myword = f.read()
            created_words.append(myword)
        else:
            created_words.append("-")
    return created_words


def create_new_game(language, seed, nr, nr_players):
    rng = random.Random(seed + str(nr) + current_app.config["SECRET_SEED"])

    tmpdir = data_dir()

    # clean up old round
    for i in range(MAX_PLAYERS):
        player_file = tmpdir / f"{seed}-{nr}-player{i}.txt"
        player_guess_file = tmpdir / f"{seed}-{nr}-player{i}-guess.txt"
        for f in [player_file, player_guess_file]:
            if f.exists():
                f.unlink()

    # load possible letters and words and shuffle
    input_file = RESOURCES / f"{language}.txt"
    with input_file.open() as f:
        data = json.load(f)
        vowels = rng.sample(data["vowels"], len(data["vowels"]))
        consonants = rng.sample(data["consonants"], len(data["consonants"]))
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

    with (tmpdir / f"{seed}-{nr}.json").open("w") as f:
        json.dump(out, f)


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
    tmpdir = data_dir()

    words, nr_players, _ = load_game_data(seed, nr)
    letters, word = load_player_data(seed, nr, player)

    # user hasn't created a word
    if not (tmpdir / f"{seed}-{nr}-player{player}.txt").exists():
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
    tmpdir = data_dir()

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

        with (tmpdir / f"{seed}-{nr}-player{player}.txt").open("w") as f:
            f.write(myword)

        return redirect(url_for("krazy.krazy_play", seed=seed, nr=nr, player=player))

    # handle user guess: for each created word, the number of the word it fits
    tmp = []
    for i in range(1, nr_players + 1):
        g = request.form.get(f"player-{player}-{i}", type=int)
        if g is not None and 1 <= g <= len(words):
            # we do need strings for writing to file later
            tmp.append(str(g))

    if len(tmp) != nr_players:
        flash("You need to assign a guess for each word")
        return redirect(url_for("krazy.krazy_play", seed=seed, nr=nr, player=player))

    if len(set(tmp)) != len(tmp):
        flash("You cannot use the same number twice")
        return redirect(url_for("krazy.krazy_play", seed=seed, nr=nr, player=player))

    with (tmpdir / f"{seed}-{nr}-player{player}-guess.txt").open("w") as f:
        f.write(",".join(tmp))

    return redirect(url_for("krazy.krazy_final", seed=seed, nr=nr, player=player))


@krazy.route("/krazy/<name:seed>/<int:nr>/<int:player>/final")
def krazy_final(seed, nr, player):
    """Show all guesses from all players."""
    tmpdir = data_dir()

    words, nr_players, language = load_game_data(seed, nr)

    # get ready for next round
    tmpdir = data_dir()
    datafile = tmpdir / f"{seed}-{nr + 1}.json"

    if not datafile.exists():
        create_new_game(language, seed, nr + 1, nr_players)

    created_words = get_list_of_created_words(seed, nr)
    player_name = [f"{w} (player{i})" for i, w in enumerate(created_words)]

    guesses = []
    for i in range(nr_players):
        player_guess_file = tmpdir / f"{seed}-{nr}-player{i}-guess.txt"
        if player_guess_file.exists():
            with player_guess_file.open("r") as f:
                guess = [int(i) for i in f.read().split(",")]
                guess_words = ["-"] * (len(words) + 1)
                for j, g in enumerate(guess):
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
    )
