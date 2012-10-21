import sublime
import sublime_plugin


class SwapBracketsCommand(sublime_plugin.WindowCommand):
    def swap_brackets(self, value):
        if value < 0:
            return

        options = []
        if len(options) == 0:
            return

        self.window.run_command(
            "bh_key", {
                "plugin": {
                    "type": ["__all__"],
                    "command": "bh_modules.swapbrackets",
                    "args": {"brackets": options[value]}
                }
            }
        )

    def run(self):
        options = []

        if len(options):
            self.window.show_quick_panel(
                options,
                self.swap_brackets
            )
