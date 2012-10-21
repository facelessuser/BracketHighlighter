import bh_plugin
import sublime


class SwapQuotes(bh_plugin.BracketPluginCommand):
    def escaped(self, idx):
        view = self.view
        escaped = False
        while idx >= 0 and view.substr(idx) == '\\':
            escaped = ~escaped
            idx -= 1
        return escaped

    def run(self, name):
        view = self.view
        quote = view.substr(self.left.begin)
        if quote != "'" and quote != '"':
            return
        new = "'" if (quote == '"') else '"'
        old = quote
        begin = self.left.begin + 1
        end = self.right.end
        edit = view.begin_edit()
        content_end = self.right.begin
        while begin < end:
            char = view.substr(begin)
            if char == old and self.escaped(begin - 1):
                view.replace(edit, sublime.Region(begin - 1, begin), '')
                end -= 1
                content_end -= 1
            elif char == new and not self.escaped(begin - 1):
                view.insert(edit, begin, "\\")
                end += 1
                content_end += 1
            begin += 1
        if name == "pyquote" and self.left.size() == 3:
            view.replace(edit, sublime.Region(self.left.begin, self.left.end), new * 3)
        else:
            view.replace(edit, sublime.Region(self.left.begin, self.left.begin + 1), new)
        if name == "pyquote" and self.right.size() == 3:
            view.replace(edit, sublime.Region(content_end, end), new * 3)
        else:
            view.replace(edit, sublime.Region(content_end, end), new)
        view.end_edit(edit)
        self.right = self.right.move(content_end, end)
        self.selection = [sublime.Region(content_end, content_end)]


def plugin():
    return SwapQuotes
