"""
BracketHighlighter.

Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import sublime


def log(msg):
    """Standard log."""

    print("BracketHighlighter: %s" % msg)


def debug(msg):
    """Debug log."""

    if sublime.load_settings("bh_core.sublime-settings").get('debug_enable', False):
        log(msg)
