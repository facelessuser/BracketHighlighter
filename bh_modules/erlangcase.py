"""
BracketHighlighter.

Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""


def validate(name, bracket, bracket_side, bfr):
    """Check if bracket is lowercase."""

    return bfr[bracket.begin:bracket.end].islower()
