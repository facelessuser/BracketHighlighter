"""
BracketHighlighter.

Copyright (c) 2013 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import BracketHighlighter.bh_plugin as bh_plugin
import sublime


class FoldBrackets(bh_plugin.BracketPluginCommand):
    """Fold bracket plugin."""

    def run(self, edit, name):
        """Fold the content between the bracket."""

        content = sublime.Region(self.left.end, self.right.begin)
        new_content = [content]
        if content.size() > 0:
            if self.view.fold(content) is False:
                new_content = self.view.unfold(content)
        self.selection = new_content


def plugin():
    """Make plugin available."""

    return FoldBrackets
