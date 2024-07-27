"""
BracketHighlighter.

Copyright (c) 2013 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import re

RE_DEF = re.compile(r"\s*(?:(?:private|public|protected)\s+)?(def).*?")
RE_DEF_ENDLESS = re.compile(
    r"^[ \t]*((?:private|public|protected)\s+)?def\s+(?:[\w\.=]+)[?!]?\s*(\([^)]+\)\s*|\s+)=",
    re.M
)
RE_KEYWORD = re.compile(r"(\s*\b)[\w\W]*")
SPECIAL_KEYWORDS = ('do',)
NORMAL_KEYWORDS = ('for', 'until', 'unless', 'while', 'class', 'module', 'if', 'begin', 'case')
RE_PREVIOUS = re.compile(r'.*([^\s])\s*=$')


def validate(view, name, bracket, bracket_side, bfr):
    """Check if bracket is lowercase."""

    b = bfr[bracket.begin:bracket.end]
    if bracket_side == 1 and b.strip() == '=':
        if view.match_selector(bracket.end, 'meta.function.parameters.default-value.ruby, string, comment'):
            return False
        view.score_selector
        left = max(0, bracket.begin - 1)
        previous = bfr[left:bracket.end]
        m = RE_PREVIOUS.match(previous)
        if m:
            s = left + m.start(1)
            selector = 'meta.function.ruby entity.name.function.ruby, meta.function.parameters.ruby'
            if not view.match_selector(s, selector):
                return False
    return True


def compare(name, first, second, bfr):
    """Differentiate 'repeat..until' from '*..end' brackets."""

    brackets = (bfr[first.begin:first.end], bfr[second.begin:second.end])
    if brackets[1].lstrip() == '=' and RE_DEF.match(brackets[0]):
        return True
    if brackets[1] == 'end':
        return True
    return False


def post_match(view, name, style, first, second, center, bfr, threshold):
    """Strip whitespace from being targeted with highlight."""

    if first is not None:
        # Strip whitespace from the beginning of first bracket
        open_bracket = bfr[first.begin:first.end]
        if open_bracket not in SPECIAL_KEYWORDS:
            open_bracket_stripped = open_bracket.strip()
            if open_bracket_stripped not in NORMAL_KEYWORDS:
                m = RE_DEF.match(open_bracket)
                if m:
                    first = first.move(first.begin + m.start(1), first.begin + m.end(1))
                    if second and bfr[second.begin:second.end].lstrip() == '=':
                        second = first
            else:
                m = RE_KEYWORD.match(open_bracket)
                if m:
                    first = first.move(first.begin + m.end(1), first.end)
    return first, second, style
