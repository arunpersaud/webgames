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
    before = int(client.get("/boggle/4x4/g/update").get_data(as_text=True))
    assert before > 0
    assert client.get("/boggle/4x4/g/start").status_code == 200
    after = int(client.get("/boggle/4x4/g/update").get_data(as_text=True))
    assert after >= before


def test_shared_link_gets_a_board(client):
    page = client.get("/boggle/5x5/neverstarted").get_data(as_text=True)
    assert len(tiles(page)) == 25
    assert int(client.get("/boggle/5x5/neverstarted/update").data) > 0


def test_restart_changes_board_time_immediately(client):
    client.post("/boggle", data={"name": "g", "size": 4})
    before = int(client.get("/boggle/4x4/g/update").data)
    client.get("/boggle/4x4/g/start")
    assert int(client.get("/boggle/4x4/g/update").data) > before


def test_no_cache_on_updates(client):
    client.post("/boggle", data={"name": "g", "size": 4})
    headers = client.get("/boggle/4x4/g/update").headers
    assert "no-store" in headers["Cache-Control"]


@pytest.mark.parametrize(
    "url", ["/boggle/9x9/g", "/boggle/9x9/g/start", "/boggle/9x9/g/update"]
)
def test_invalid_size(client, url):
    assert client.get(url).status_code == 404


@pytest.mark.parametrize("data", [{"name": "g", "size": 6}, {"name": "g"}])
def test_invalid_form(client, data):
    assert client.post("/boggle", data=data).status_code == 400


def test_empty_name(client):
    response = client.post("/boggle", data={"name": "!", "size": 4})
    assert response.headers["Location"] == "/boggle"
