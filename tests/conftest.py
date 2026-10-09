import pytest

from games import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "SECRET_SEED": "test-secret-seed",
            "DATABASE": tmp_path / "test.sqlite",
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()
