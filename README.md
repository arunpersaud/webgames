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
    uv run flask --app games run --debug

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting. To run it
automatically on every commit: `uvx pre-commit install`.
