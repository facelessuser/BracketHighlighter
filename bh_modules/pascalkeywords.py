"""
BracketHighlighter.

Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
from BracketHighlighter.bh_plugin import import_module


def compare(name, first, second, bfr):
    """Differentiate 'repeat..until' and 'unit..end.' from '*..end' brackets."""
    brackets = (bfr[first.begin:first.end], bfr[second.begin:second.end])
    return (brackets[0] == "repeat" and brackets[1] == "until") \
        or (brackets[0] == "unit" and brackets[1] == "end.") \
        or (brackets[0] != "repeat" and brackets[0] != "unit" and (brackets[1] == "end"))
