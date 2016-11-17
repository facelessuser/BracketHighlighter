"""
BracketHighlighter.

Copyright (c) 2013 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import sublime
import BracketHighlighter.bh_plugin as bh_plugin
from BracketHighlighter.bh_plugin import import_module
tags = import_module("bh_modules.tags")


class TagNameSelect(bh_plugin.BracketPluginCommand):
    """Tag name select plugin."""

    def run(self, edit, name):
        """Select tag name."""

        if self.left.size() > 1:
            tag_settings = sublime.load_settings("bh_tag.sublime-settings")
            tag_mode = tags.get_tag_mode(self.view, tag_settings.get("tag_mode", []))
            tag_name = tag_settings.get('tag_name')[tag_mode]
            region1 = self.view.find(tag_name, self.left.begin)
            region2 = self.view.find(tag_name, self.right.begin)
            self.selection = [region1, region2]


def plugin():
    """Make plugin available."""

    return TagNameSelect
