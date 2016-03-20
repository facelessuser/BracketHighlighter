"""
BracketHighlighter.

Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""


def post_match(view, name, style, first, second, center, bfr, threshold):
    """Ensure that backticks inside the inline are not highlighted."""
    inline_content_scope = "markup.raw.inline.content.markdown"
    # move the first scope back to the left
    if first is not None:
        end = first.end
        while view.score_selector(end - 1, inline_content_scope):
            end -= 1
        first = first.move(first.begin, end)
    return first, second, style
