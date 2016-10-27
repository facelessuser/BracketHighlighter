"""
BracketHighlighter.

Copyright (c) 2013 - 2016 Deathaxe <deathaxe82@gmail.com>
License: MIT
"""

S840D_HMI_CLASSES = ("//a", "//b", "//g", "//m", "//s")


def compare(name, first, second, bfr):
    """Ensure correct open is paired with correct close."""

    o = bfr[first.begin:first.end].lower()
    c = bfr[second.begin:second.end].lower()

    match = False
    # classes
    if o in S840D_HMI_CLASSES and c == "//end":
        match = True
    # methods
    elif c == "end_" + o:
        match = True
    return match
