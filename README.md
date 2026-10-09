# webgames

## A collection of games to play with other humans on the internet.

### Contributors:
* Arun Persaud  [https://github.com/arunpersaud](https://github.com/arunpersaud)
* Sean Brennan  [https://github.com/zettix](https://github.com/zettix)
* Lance Thornton [Sure looks like Lance](https://github.com/lancethornton)

Vision: Webify common board games so friends can play with each other using the internet and video conferencing.


## Games:
* Boggle clone:
** Standard (4x4)
** Big(5x5)
* Doppelkopf


# Source
The source can be found on [github](https://github.com/arunpersaud/webgames). Pull requests welcome.

Development uses [uv](https://docs.astral.sh/uv/):

    uv sync                 # create .venv with all dependencies
    uv run pytest           # run the tests
    uv run flask --app games run --debug   # http://localhost:5000

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting. To run it
automatically on every commit: `uvx pre-commit install`.

# Deployment

The `Containerfile` builds a production image (Python 3.14, gunicorn on
port 8000, dependencies from `uv.lock`):

    podman build -t webgames .
    podman run -p 8000:8000 -v ./data:/data \
        -e FLASK_SECRET_KEY=... -e FLASK_SECRET_SEED=... webgames

Game state is kept in `/data/webgames.sqlite`; games untouched for a week
are deleted.
