import os
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


class _Config:
    DEBUG = False
    TESTING = True
    SECRET_KEY = "test-secret-key"
    SECRET_SEED = "test-secret-seed"


# the app imports games/config.py (gitignored); provide it without a file
_config = types.ModuleType("games.config")
_config.ProductionConfig = _config.DevelopmentConfig = _Config
sys.modules["games.config"] = _config


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Test client with fresh game state.

    The app keeps state in ./tmp and reads ./games/krazy/resource, both
    relative to the working directory.
    """
    (tmp_path / "tmp").mkdir()
    (tmp_path / "tmp" / "doko.db").touch()
    (tmp_path / "tmp" / "skat.db").touch()
    os.symlink(ROOT / "games", tmp_path / "games")
    monkeypatch.chdir(tmp_path)

    from games import app

    return app.test_client()
