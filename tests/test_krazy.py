import re

import pytest


def start(client, players=3):
    return client.post(
        "/krazy", data={"name": "Krazy 1", "players": players, "language": "de"}
    )


def letters(page):
    block = page.split('id="sortableList"')[1].split("</ul>")[0]
    return re.findall(r"<li>(\w)</li>", block)


def test_start_game(client):
    page = start(client).get_data(as_text=True)
    assert re.findall(r"/krazy/krazy1/1/(\d)", page) == ["0", "1", "2"]


@pytest.mark.parametrize("players", [0, 8, 10**9])
def test_player_limit(client, players):
    assert start(client, players).status_code == 400


@pytest.mark.parametrize(
    "url", ["/krazy/nothere/1/0", "/krazy/krazy1/1/3", "/krazy/krazy1/x/0"]
)
def test_invalid_urls(client, url):
    start(client)
    assert client.get(url).status_code == 404


@pytest.mark.parametrize(
    "data",
    [
        {"name": "k", "players": "x", "language": "de"},
        {"name": "k", "players": 3, "language": "xx"},
        {"name": "k", "language": "de"},
    ],
)
def test_invalid_start_form(client, data):
    assert client.post("/krazy", data=data).status_code == 400


def test_out_of_range_guess(client):
    start(client)
    client.post("/krazy/krazy1/1/0", data={"myword": ""})
    data = {"player-0-1": 1, "player-0-2": 2, "player-0-3": 99}
    response = client.post("/krazy/krazy1/1/0", data=data, follow_redirects=True)
    assert "assign a guess for each word" in response.get_data(as_text=True)


def test_full_round(client):
    start(client)
    # each player builds a word from their letters
    for p in range(3):
        page = client.get(f"/krazy/krazy1/1/{p}").get_data(as_text=True)
        mine = letters(page)
        assert len(mine) == 9
        response = client.post(
            f"/krazy/krazy1/1/{p}", data={"myword": "".join(mine[:3])}
        )
        assert response.status_code == 302

    # every player assigns each created word to a different word number
    for p in range(3):
        page = client.get(f"/krazy/krazy1/1/{p}").get_data(as_text=True)
        data, used = {}, set()
        for name, options in re.findall(
            r'<select name="([\w-]+)"[^>]*>(.*?)</select>', page, re.S
        ):
            value = next(
                v for v in re.findall(r'value="(\d+)"', options) if v not in used
            )
            used.add(value)
            data[name] = value
        assert len(data) == 3
        response = client.post(f"/krazy/krazy1/1/{p}", data=data)
        assert response.headers["Location"] == f"/krazy/krazy1/1/{p}/final"

    final = client.get("/krazy/krazy1/1/0/final")
    assert final.status_code == 200
    page = final.get_data(as_text=True)
    assert "end of round 1" in page
    assert page.count("(player") == 3  # one row per guess
    # the next round is prepared
    assert client.get("/krazy/krazy1/2").status_code == 200


def test_wrong_letters_are_rejected(client):
    start(client)
    response = client.post("/krazy/krazy1/1/0", data={"myword": "qqqqqqqqqqqq"})
    assert response.status_code == 302
    page = client.get("/krazy/krazy1/1/0").get_data(as_text=True)
    assert "not in your list of letters" in page


@pytest.mark.parametrize("players", [1, 3, 7])
def test_every_player_gets_nine_letters(client, players):
    start(client, players)
    for p in range(players):
        page = client.get(f"/krazy/krazy1/1/{p}").get_data(as_text=True)
        assert len(letters(page)) == 9


def test_new_game_with_old_name_starts_over(client):
    start(client)
    client.post("/krazy/krazy1/1/0", data={"myword": ""})
    client.get("/krazy/krazy1/1/0/final")  # creates round 2
    start(client)
    assert client.get("/krazy/krazy1/2").status_code == 404
    page = client.get("/krazy/krazy1/1/0").get_data(as_text=True)
    assert 'id="sortableList"' in page  # player 0 has to build a word again


def test_status_changes_with_guesses(client):
    start(client)
    assert client.get("/krazy/nothere/1/status").status_code == 404
    assert client.get("/krazy/krazy1/1/status").json == {"version": ""}
    page = client.get("/krazy/krazy1/1/0/final").get_data(as_text=True)
    assert 'data-poll="/krazy/krazy1/1/status"' in page

    for p in range(3):  # everyone builds an empty word
        client.post(f"/krazy/krazy1/1/{p}", data={"myword": ""})
    assert client.get("/krazy/krazy1/1/status").json == {"version": ""}

    page = client.get("/krazy/krazy1/1/2").get_data(as_text=True)
    selects = re.findall(r'<select name="([\w-]+)"[^>]*>(.*?)</select>', page, re.S)
    data, used = {}, set()
    for name, options in selects:
        value = next(v for v in re.findall(r'value="(\d+)"', options) if v not in used)
        used.add(value)
        data[name] = value
    client.post("/krazy/krazy1/1/2", data=data)
    assert client.get("/krazy/krazy1/1/status").json == {"version": "2"}
