import bh_plugin
import sublime

DEFAULT_TAGS = ["cfml", "html", "angle"]


class SelectBracket(bh_plugin.BracketPluginCommand):
    def run(self, edit, name, select='', tags=DEFAULT_TAGS):
        current_left, current_right = self.selection[0].begin(), self.selection[0].end()
        left, right = self.left, self.right
        first, last = left.end, right.begin
        if select == 'left':
            if name in tags and left.size() > 1:
                first, last = left.begin + 1, left.begin + 1
                if first == current_left and last == current_right:
                    first, last = left.begin, left.begin
            else:
                first, last = left.end, left.end
                if first == current_left and last == current_right:
                    first, last = left.begin, left.begin
        elif select == 'right':
            if left.end != right.end:
                if name in tags and left.size() > 1:
                    first, last = right.begin + 1, right.begin + 1
                    if first == current_left and last == current_right:
                        first, last = right.end, right.end
                else:
                    first, last = right.begin, right.begin
                    if first == current_left and last == current_right:
                        first, last = right.end, right.end
            else:
                # There is no second bracket, so just select the first
                if name in tags and left.size() > 1:
                    first, last = left.begin + 1, left.begin + 1
                else:
                    first, last = right.end, right.end
                    if first == current_left and last == current_right:
                        first, last = right.end, right.end
        elif first == current_left and last == current_right:
            first, last = left.begin, right.end

        self.selection = [sublime.Region(first, last)]


def plugin():
    return SelectBracket
