import bh_plugin
import sublime


class SwapBrackets(bh_plugin.BracketPluginCommand):
    def calculate_indentation(self, sel):
        # Calculate how far the last bracket is indented
        _, col_position = self.view.rowcol(self.right.begin)
        tab_size = self.view.settings().get("tab_size", 4)
        tab_count = self.view.substr(sublime.Region(self.right.begin - col_position, self.right.begin)).count('\t')
        spaces = col_position - tab_count
        return "\t" * tab_count + "\t" * (spaces / tab_size) + " " * (spaces % tab_size if spaces >= tab_size else spaces)

    def run(self, edit, name, brackets=None):
        if brackets is None:
            return

        # Prepare selections
        sel = self.selection[0]
        new_sel = [sublime.Region(sel.begin() + len(brackets[0]))]

        # Swap the brackets
        self.view.replace(edit, self.right.toregion(), brackets[-1])
        if len(brackets) > 2:
            # Set up indentation and insertion points
            insert_point = self.right.begin
            indent_to_col = self.calculate_indentation(sel)
            for b in reversed(brackets[1:len(brackets) - 1]):
                    self.view.replace(edit, sublime.Region(insert_point), b + "\n" + indent_to_col)
        self.view.replace(edit, self.left.toregion(), brackets[0])

        self.selection = new_sel


def plugin():
    return SwapBrackets
