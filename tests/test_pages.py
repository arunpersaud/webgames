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


def test_secrets_required_in_production(monkeypatch):
    from games import create_app

    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    monkeypatch.delenv("FLASK_SECRET_SEED", raising=False)
    with pytest.raises(RuntimeError, match="FLASK_SECRET_KEY"):
        create_app()


def test_config_from_environment(monkeypatch, tmp_path):
    from games import create_app

    monkeypatch.setenv("FLASK_SECRET_KEY", "k")
    monkeypatch.setenv("FLASK_SECRET_SEED", "s")
    monkeypatch.setenv("FLASK_DATABASE", str(tmp_path / "games.sqlite"))
    app = create_app()
    assert app.config["SECRET_SEED"] == "s"
    assert (tmp_path / "games.sqlite").exists()
