import pytest


@pytest.mark.parametrize("url", ["/", "/doko", "/skat", "/boggle", "/krazy"])
def test_start_pages(client, url):
    assert client.get(url).status_code == 200


def test_security_headers(client):
    headers = client.get("/").headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "SAMEORIGIN"


def test_static_files(client):
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/games/boggle/static/boggle.js").status_code == 200
