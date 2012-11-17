import sublime_plugin
from collections import namedtuple

MENU = namedtuple("Menu", "simple content block block_indent")(
    "Remove Brackets",
    "Remove Brackets and Content",
    "Remove Brackets: Block",
    "Remove Brackets: Indented Block"
)


class BhRemoveBracketsCommand(sublime_plugin.WindowCommand):
    """
    Command to remove current highlighted brackets and optionally content
    """

    def remove_brackets(self, value):
        """
        Perform removal of brackets
        """

        if value != -1:
            menu_item = MENU[value]
            indent = menu_item == MENU.block_indent
            block = menu_item == MENU.block or menu_item == MENU.block_indent
            content = menu_item == MENU.content

            self.window.run_command(
                "bh_key",
                {
                    "plugin": {
                        "type": ["__all__"],
                        "command": "bh_modules.bracketremove",
                        "args": {
                            "remove_indent": indent,
                            "remove_block": block,
                            "remove_content": content
                        }
                    }
                }
            )

    def run(self):
        """
        Show menu of removal options
        """

        self.window.show_quick_panel(
            list(MENU),
            self.remove_brackets
        )
