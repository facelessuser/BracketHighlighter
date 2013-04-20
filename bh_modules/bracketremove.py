import bh_plugin
import re
import sublime


class BracketRemove(bh_plugin.BracketPluginCommand):
    def decrease_indent_level(self, edit, row_first, row_last):
        tab_size = self.view.settings().get("tab_size", 4)
        indents = re.compile(r"^(?:\t| {%d}| *)((?:\t| {%d}| )*)([\s\S]*)" % (tab_size, tab_size))
        if not self.single_line:
            for x in reversed(range(row_first, row_last + 1)):
                line = self.view.full_line(self.view.text_point(x, 0))
                text = self.view.substr(line)
                m = indents.match(text)
                if m:
                    self.view.replace(edit, line, m.group(1) + m.group(2))

    def run(self, edit, name, remove_content=False, remove_indent=False, remove_block=False):
        if remove_content:
            self.view.replace(edit, sublime.Region(self.left.begin, self.right.end), "")
        else:
            row_first = self.view.rowcol(self.left.end)[0] + 1
            row_last = self.view.rowcol(self.right.begin)[0] - 1
            self.single_line = not row_first <= row_last
            if remove_block and not self.single_line:
                self.view.replace(edit, self.view.full_line(self.right.toregion()), "")
            else:
                self.view.replace(edit, self.right.toregion(), "")
            if remove_indent:
                self.decrease_indent_level(edit, row_first, row_last)
            if remove_block and not self.single_line:
                self.view.replace(edit, self.view.full_line(self.left.toregion()), "")
            else:
                self.view.replace(edit, self.left.toregion(), "")

        self.left = None
        self.right = None
        self.nobracket = True


def plugin():
    return BracketRemove
