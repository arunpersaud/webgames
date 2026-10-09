import re
from pathlib import Path

import pytest


@pytest.mark.parametrize("url", ["/", "/doko", "/skat", "/boggle", "/krazy"])
def test_start_pages(client, url):
    assert client.get(url).status_code == 200


def test_security_headers(client):
    headers = client.get("/").headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    csp = headers["Content-Security-Policy"]
    assert "default-src 'none'" in csp
    assert "script-src 'self';" in csp
    assert "unsafe" not in csp


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


TEMPLATES = sorted(Path(__file__).parent.parent.glob("games/**/templates/*.html"))


@pytest.mark.parametrize("template", TEMPLATES, ids=lambda p: p.name)
def test_no_inline_code(template):
    """The CSP blocks inline scripts, styles and event handlers."""
    html = template.read_text()
    assert not re.search(r"<script(?![^>]*\bsrc=)", html)
    assert "<style" not in html
    assert not re.search(r"\sstyle=", html)
    assert not re.search(r"\son[a-z]+=", html)


@pytest.mark.parametrize("template", TEMPLATES, ids=lambda p: p.name)
def test_no_external_resources(template):
    html = template.read_text()
    assert not re.search(r'<(script|link|img)[^>]+(src|href)="(https?:)?//', html)


def test_only_web_assets_in_static():
    """Everything under static/ is public; keep scripts and notes elsewhere."""
    root = Path(__file__).parent.parent / "games"
    allowed = {".css", ".js", ".png", ".svg", ".ico"}
    for path in root.glob("**/static/**/*"):
        if path.is_file():
            assert path.suffix in allowed, path
