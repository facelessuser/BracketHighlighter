"""
BracketHighlighter.

Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
from BracketHighlighter.bh_plugin import ImportModule as ImpMod
lowercase = ImpMod.import_module("bh_modules.lowercase")


def validate(*args):
    """Check if bracket is lowercase."""
    return lowercase.validate(*args)


def compare(name, first, second, bfr):
    """Differentiate 'repeat..until' from '*..end' brackets."""
    brackets = (bfr[first.begin:first.end], bfr[second.begin:second.end])
    return (brackets[0] == "repeat") ^ (brackets[1] == "end")
