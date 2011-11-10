import bracket_plugin
import sublime


class swap_brackets(bracket_plugin.BracketPluginCommand):
    brackets = None

    def swap_brackets(self, value):
        brackets = [
            ["[", "]"],
            ["(", ")"],
            ["<", ">"],
            ["{", "}"]
        ]
        edit = self.view.begin_edit()
        self.view.replace(edit, sublime.Region(self.brackets.begin(), self.brackets.begin() + 1), brackets[value][0])
        self.view.replace(edit, sublime.Region(self.brackets.end() - 1, self.brackets.end()), brackets[value][1])
        self.view.end_edit(edit)

    def run(self, bracket, content, selection):
        self.brackets = bracket

        self.view.window().show_quick_panel(
            [
                "[] square", "() round",
                "<> angle", "{} curly"
            ],
            self.swap_brackets
        )
