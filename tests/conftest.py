import pytest

from games import create_app


@pytest.fixture
def app(tmp_path):
    (tmp_path / "doko.db").touch()
    (tmp_path / "skat.db").touch()
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "SECRET_SEED": "test-secret-seed",
            "DATA_DIR": tmp_path,
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()
