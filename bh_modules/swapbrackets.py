"""
BracketHighlighter.

Copyright (c) 2013 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import sublime
from BracketHighlighter.bh_plugin import import_module
BracketRemove = import_module("bh_modules.bracketremove", "BracketRemove")


class SwapBrackets(BracketRemove):
    """Swap bracket plugin."""

    def run(self, edit, name, remove_content=False, remove_indent=False, remove_block=False):
        """Remove then replace the bracket and adjust indentation if desired."""

        offset = self.left.toregion().size()
        selection = [sublime.Region(self.left.begin, self.right.begin - offset)]
        left = self.left.move(self.left.end, self.left.end)
        right = self.right.move(self.right.begin, self.right.begin)
        super(SwapBrackets, self).run(edit, name)
        self.selection = selection
        self.left = left
        self.right = right
        self.nobracket = False


def plugin():
    """Make plugin available."""

    return SwapBrackets
