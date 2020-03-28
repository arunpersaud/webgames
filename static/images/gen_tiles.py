#!/usr/bin/env python
"""
Create letter tiles for use with web games.

Geneates boggle like letters, with qu highlighted.
"""

import os


def substitute(letter):
    if letter == "Q":
        return "Qu"
    return letter


def getParams(letter):
    bone = "\#eaeaea"
    brown = "\#753010"
    dark = "\#332222"
    params = {}
    if letter == "Qu":
        params["background_color"] = brown
        params["fill_color"] = bone
    else:
        params["background_color"] = dark
        params["fill_color"] = bone

    params["letter"] = letter
    params["point_size"] = 62
    params["font"] = "helvetica-bold"
    params["xdim"] = 100
    params["ydim"] = 100
    params["filename"] = f"tile_{letter}.png"

    return params


def genCommand(params):
    command_template = (
        "convert -background {background_color}"
        " -fill {fill_color} -font {font}"
        " -gravity center"
        " -border 4 -bordercolor darkgreen"
        " -pointsize {point_size}"
        " -size {xdim}x{ydim} label:{letter} {filename}"
    )
    return command_template.format(**params)


alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
assert len(alphabet) == 26
letters = [substitute(x) for x in alphabet]

for letter in letters:
    params = getParams(letter)
    cmd = genCommand(params)
    os.system(cmd)
    print(cmd)
