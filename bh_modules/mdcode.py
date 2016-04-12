"""
BracketHighlighter.

Copyright (c) 2013 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""


def post_match(view, name, style, first, second, center, bfr, threshold):
    """Ensure that backticks that do not contribute inside the inline or block regions are not highlighted."""

    if first is not None and second is not None:
        diff = first.size() - second.size()
        if diff > 0:
            first = first.move(first.begin, first.end - diff)
        elif diff < 0:
            second = second.move(second.begin - diff, second.end)
    return first, second, style
