"""
BracketHighlighter.

Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""


def validate(name, bracket, bracket_side, bfr):
    """Check if bracket is lowercase."""
    return bfr[bracket.begin:bracket.end].islower()


def compare(name, first, second, bfr):
    """Differentiate 'repeat..until' from '*..end' brackets."""
    brackets = (bfr[first.begin:first.end], bfr[second.begin:second.end])
    return (brackets[0] == "repeat") ^ (brackets[1] == "end")
