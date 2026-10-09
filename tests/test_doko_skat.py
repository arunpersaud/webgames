import re
from collections import Counter

import pytest


def hand(client, game, seed, nr, player):
    """Cards shown to a player (first list on the page, before the by-suit one)."""
    response = client.get(f"/{game}/{seed}/{nr}/{player}")
    assert response.status_code == 200
    html = response.get_data(as_text=True).split("sorted by suit")[0]
    return [int(c) for c in re.findall(rf"/{game}/(\d+)\.png", html)]


def test_start_session_sanitizes_name(client):
    response = client.post("/doko", data={"name": "My Game!"})
    assert response.status_code == 302
    assert response.headers["Location"] == "/doko/mygame/1/"


def test_doko_deal(client):
    hands = [hand(client, "doko", "s1", 1, p) for p in "ABCD"]
    assert all(len(h) == 12 for h in hands)
    # 24 different card images, each card twice in the deck
    counts = Counter(c for h in hands for c in h)
    assert len(counts) == 24
    assert set(counts.values()) == {2}


def test_skat_deal(client):
    hands = [hand(client, "skat", "s1", 1, p) for p in ["A", "B", "C", "skat"]]
    assert [len(h) for h in hands] == [10, 10, 10, 2]
    assert sorted(c for h in hands for c in h) == list(range(32))


def test_hand_can_be_seen_only_once(client):
    hand(client, "doko", "s1", 1, "A")
    page = client.get("/doko/s1/1/A").get_data(as_text=True)
    assert "already been used" in page
    overview = client.get("/doko/s1/1/").get_data(as_text=True)
    assert overview.count("(viewed)") == 1
    assert overview.count("(not viewed)") == 3


def test_deals_differ_per_game_and_session(client):
    assert hand(client, "doko", "s1", 1, "A") != hand(client, "doko", "s1", 2, "A")
    assert hand(client, "doko", "s1", 3, "A") != hand(client, "doko", "s2", 3, "A")


def test_deal_is_deterministic(client, tmp_path):
    first = hand(client, "doko", "s1", 1, "A")
    (tmp_path / "doko.db").write_text("")  # forget the "seen" tag
    assert hand(client, "doko", "s1", 1, "A") == first


@pytest.mark.parametrize(
    "url",
    [
        "/doko/s1/1/E",
        "/skat/s1/1/D",
        "/doko/s%0A1/1/A",
        "/doko/s1/x/A",
        "/doko/s1/-1/A",
        "/doko/s_1/1/A",
        "/poker",
        "/favicon.ico",
    ],
)
def test_invalid_urls(client, url):
    assert client.get(url).status_code == 404


def test_deal_does_not_touch_global_random(client):
    import random

    state = random.getstate()
    hand(client, "doko", "s1", 1, "A")
    assert random.getstate() == state


def test_empty_session_name(client):
    response = client.post("/skat", data={"name": "!?"}, follow_redirects=True)
    assert response.request.path == "/skat"
    assert "Please enter a session name" in response.get_data(as_text=True)
