import sys, os

INTERP = "/home/arun/bin/python3.9"

# INTERP is present twice so that the new python interpreter knows the actual executable path
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

from games import app as application

if __name__ == "__main__":
    application.run(debug=True)
