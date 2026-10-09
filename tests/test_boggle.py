import re

import pytest


def tiles(page):
    return re.findall(r"tile_([A-Za-z]+)\.png", page)


@pytest.mark.parametrize("size", [4, 5])
def test_create_game(client, size):
    response = client.post("/boggle", data={"name": "Fun Game", "size": size})
    assert response.status_code == 302
    assert response.headers["Location"] == f"/boggle/{size}x{size}/fungame"

    page = client.get(f"/boggle/{size}x{size}/fungame").get_data(as_text=True)
    assert len(tiles(page)) == size * size


def test_restart_changes_timestamp(client):
    client.post("/boggle", data={"name": "g", "size": 4})
    before = client.get("/boggle/4x4/g/update").json["started"]
    assert before > 0
    response = client.post("/boggle/4x4/g/start")
    assert response.headers["Location"] == "/boggle/4x4/g"
    after = client.get("/boggle/4x4/g/update").json["started"]
    assert after >= before


def test_shared_link_gets_a_board(client):
    page = client.get("/boggle/5x5/neverstarted").get_data(as_text=True)
    assert len(tiles(page)) == 25
    assert client.get("/boggle/5x5/neverstarted/update").json["started"] > 0


def test_restart_changes_board_time_immediately(client):
    client.post("/boggle", data={"name": "g", "size": 4})
    before = client.get("/boggle/4x4/g/update").json["started"]
    client.post("/boggle/4x4/g/start")
    assert client.get("/boggle/4x4/g/update").json["started"] > before


def test_no_cache_on_updates(client):
    client.post("/boggle", data={"name": "g", "size": 4})
    headers = client.get("/boggle/4x4/g/update").headers
    assert "no-store" in headers["Cache-Control"]


@pytest.mark.parametrize(
    "url", ["/boggle/9x9/g", "/boggle/9x9/g/update", "/boggle/4x4/nothere/update"]
)
def test_invalid_size(client, url):
    assert client.get(url).status_code == 404


@pytest.mark.parametrize("data", [{"name": "g", "size": 6}, {"name": "g"}])
def test_invalid_form(client, data):
    assert client.post("/boggle", data=data).status_code == 400


def test_empty_name(client):
    response = client.post("/boggle", data={"name": "!", "size": 4})
    assert response.headers["Location"] == "/boggle"


def test_start_needs_post(client):
    """A link preview or crawler must not reset the board."""
    assert client.get("/boggle/4x4/g/start").status_code == 405


def test_timer_counts_from_board_start(app, client):
    from games.db import get_db

    client.post("/boggle", data={"name": "g", "size": 4})
    with app.app_context():
        get_db().execute("UPDATE boggle SET started = started - 60000")
    page = client.get("/boggle/4x4/g").get_data(as_text=True)
    assert 'data-seconds="120"' in page


def test_no_jquery(client):
    client.post("/boggle", data={"name": "g", "size": 4})
    page = client.get("/boggle/4x4/g").get_data(as_text=True)
    assert "jquery" not in page.lower()
