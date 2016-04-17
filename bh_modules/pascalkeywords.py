"""
BracketHighlighter.

Copyright (c) 2013 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""


def compare(name, first, second, bfr):
    """Differentiate 'repeat..until' from '*..end' brackets."""
    brackets = (bfr[first.begin:first.end], bfr[second.begin:second.end])
    return (brackets[0] == "repeat") ^ (brackets[1] == "end")
