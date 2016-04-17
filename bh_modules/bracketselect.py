"""
BracketHighlighter.

Copyright (c) 2013 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import BracketHighlighter.bh_plugin as bh_plugin
import sublime

DEFAULT_TAGS = ["cfml", "html", "angle"]


class SelectBracket(bh_plugin.BracketPluginCommand):
    """Select Bracket plugin."""

    def run(self, edit, name, select='', tags=None, always_include_brackets=False, alternate=False):
        """
        Select the content between brackets.

        If "always_include_brackets" is enabled,
        include the brackts as well.  If the content is already selected, expand to the
        parent.
        """

        self.tags = DEFAULT_TAGS if tags is None else tags
        self.current_left, self.current_right = self.selection[0].begin(), self.selection[0].end()
        first, last = self.left.end, self.right.begin

        if select == 'left':
            first, last = self.select_left(name, first, last, alternate)
        elif select == 'right':
            first, last = self.select_right(name, first, last, alternate)
        elif first == self.current_left and last == self.current_right or always_include_brackets:
            first, last = self.select_expand(first, last)

        self.selection = [sublime.Region(first, last)]

    def select_left(self, name, first, last, alternate):
        """Select the left bracket."""

        if name in self.tags and self.left.size() > 1:
            first, last = self.left.begin + 1, self.left.begin + 1
            if first == self.current_left and last == self.current_right:
                self.refresh_match = True
                if alternate:
                    first, last = self.right.begin + 1, self.right.begin + 1
                else:
                    first, last = self.left.begin, self.left.begin
        else:
            first, last = self.left.end, self.left.end
            if first == self.current_left and last == self.current_right:
                self.refresh_match = True
                if alternate:
                    first, last = self.right.begin, self.right.begin
                else:
                    first, last = self.left.begin, self.left.begin
        return first, last

    def select_right(self, name, first, last, alternate):
        """Select the right bracket."""

        if self.left.end != self.right.end:
            if name in self.tags and self.left.size() > 1:
                first, last = self.right.begin + 1, self.right.begin + 1
                if first == self.current_left and last == self.current_right:
                    self.refresh_match = True
                    if alternate:
                        first, last = self.left.begin + 1, self.left.begin + 1
                    else:
                        first, last = self.right.end, self.right.end
            else:
                first, last = self.right.begin, self.right.begin
                if first == self.current_left and last == self.current_right:
                    self.refresh_match = True
                    if alternate:
                        first, last = self.left.end, self.left.end
                    else:
                        first, last = self.right.end, self.right.end
        else:
            # Select the first because there is no second bracket.
            if name in self.tags and self.left.size() > 1:
                first, last = self.left.begin + 1, self.left.begin + 1
                if first == self.current_left and last == self.current_right:
                    self.refresh_match = True
                    if not alternate:
                        first, last = self.left.end, self.left.end
            else:
                first, last = self.right.end, self.right.end
                if first == self.current_left and last == self.current_right:
                    self.refresh_match = True
                    if not alternate:
                        first, last = self.right.end, self.right.end
        return first, last

    def select_expand(self, first, last):
        """Expand content selection."""

        first, last = self.left.begin, self.right.end
        self.refresh_match = True
        return first, last


def plugin():
    """Make plugin available."""

    return SelectBracket
