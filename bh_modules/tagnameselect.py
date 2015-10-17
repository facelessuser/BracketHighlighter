"""
BracketHighlighter.

Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import BracketHighlighter.bh_plugin as bh_plugin


class TagNameSelect(bh_plugin.BracketPluginCommand):
    """Tag name select plugin."""

    def run(self, edit, name):
        """Select tag name."""

        if self.left.size() > 1:
            tag_name = '[\w\:\.\-]+'
            region1 = self.view.find(tag_name, self.left.begin)
            region2 = self.view.find(tag_name, self.right.begin)
            self.selection = [region1, region2]


def plugin():
    """Make plugin available."""

    return TagNameSelect
