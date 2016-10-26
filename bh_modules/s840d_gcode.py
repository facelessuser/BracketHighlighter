"""
BracketHighlighter.

Copyright (c) 2013 - 2016 Deathaxe <deathaxe82@gmail.com>
License: MIT
"""


def compare(name, first, second, bfr):
    """Ensure correct open is paired with correct close."""

    o = bfr[first.begin:first.end].lower()
    c = bfr[second.begin:second.end].lower()

    match = False
    if o == "repeat" and c == "until":
        match = True
    elif c == "end" + o:
        match = True
    return match
