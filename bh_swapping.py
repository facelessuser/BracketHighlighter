import sublime_plugin
import bh_wrapping


class SwapBrackets(bh_wrapping.WrapBrackets):
    def wrap(self, wrap_entry):
        if wrap_entry < 0:
            return

        self._style = ["inline"]

        self.brackets = self._brackets[wrap_entry]
        self.wrap_brackets(0)


class SwapBracketsCommand(sublime_plugin.WindowCommand):
    def swap_brackets(self, value):
        if value < 0:
            return

        self.brackets = self.wrap._brackets[value]

        self.window.run_command(
            "bh_key",
            {
                "plugin": {
                    "type": ["__all__"],
                    "command": "bh_modules.swapbrackets"
                }
            }
        )
        self.wrap.wrap(value)

    def run(self):
        view = self.window.active_view()
        if view is None:
            return
        self.wrap = SwapBrackets(view, "bh_swapping.sublime-settings", "swapping")

        if len(self.wrap._menu):
            self.window.show_quick_panel(
                self.wrap._menu,
                self.swap_brackets
            )
