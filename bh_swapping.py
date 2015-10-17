"""
BracketHighlighter.

Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import sublime
import sublime_plugin
import BracketHighlighter.bh_wrapping as bh_wrapping


class SwapBrackets(bh_wrapping.WrapBrackets):
    """
    Swap Base Class.

    Swap base is derived from the wrap base.
    """

    def wrap(self, wrap_entry):
        """Setup for wrapping."""

        if wrap_entry < 0:
            return

        self._style = ["inline"]

        self.brackets = self._brackets[wrap_entry]
        self.wrap_brackets(0)


class SwapBracketsCommand(sublime_plugin.WindowCommand):
    """Swap bracket command."""

    def finalize(self, callback):
        """Execute post wrap callback."""

        if self.view is not None:
            if not self.view.settings().get("BracketHighlighterBusy", False):
                callback()
            else:
                sublime.set_timeout(lambda: self.finalize(callback), 100)

    def swap_brackets(self, value):
        """Swap the brackets."""

        if value < 0:
            return

        self.brackets = self.wrap._brackets[value]

        self.window.run_command(
            "bh_async_key" if self.async else "bh_key",
            {
                "plugin": {
                    "type": ["__all__"],
                    "command": "bh_modules.swapbrackets"
                }
            }
        )

        self.view = self.window.active_view()

        if self.async:
            sublime.set_timeout(lambda: self.finalize(lambda: self.wrap.wrap(value)), 100)
        else:
            self.finalize(self.wrap.wrap(value))

    def run(self, async=False):
        """Initiate the swap."""

        self.async = async
        view = self.window.active_view()
        if view is None:
            return
        self.wrap = SwapBrackets(view, "bh_swapping.sublime-settings", "swapping")

        if len(self.wrap._menu):
            self.window.show_quick_panel(
                self.wrap._menu,
                self.swap_brackets
            )
