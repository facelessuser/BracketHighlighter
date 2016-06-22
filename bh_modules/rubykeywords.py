"""
BracketHighlighter.

Copyright (c) 2013 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import re

RE_DEF = re.compile(r"\s*(?:(?:private|public|protected)\s+)?(def)(\s+.*)?")
SPECIAL_KEYWORDs = ('do')
NORMAL_KEYWORDS = ('for', 'until', 'unless', 'while', 'class', 'module', 'if', 'begin', 'case')



def post_match(view, name, style, first, second, center, bfr, threshold):
    """Strip whitespace from being targeted with highlight."""

    if first is not None:
        # Strip whitespace from the beginning of first bracket
        open_bracket = bfr[first.begin:first.end]
        if open_bracket != SPECIAL_KEYWORDs:
            open_bracket = open_bracket.strip()
            if open_bracket not in NORMAL_KEYWORDS:
                m = RE_DEF.match(open_bracket)
                if m:
                    first = first.move(first.begin + m.start(1), first.begin + m.end(1))
    return first, second, style
