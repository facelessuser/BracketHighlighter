import sublime
from bh_plugin import ImportModule as ImpMod
BracketRemove = ImpMod.import_from("bh_modules.bracketremove", "BracketRemove")


class SwapBrackets(BracketRemove):
    def run(self, edit, name, remove_content=False, remove_indent=False, remove_block=False):
        offset = self.left.toregion().size()
        selection = [sublime.Region(self.left.begin, self.right.begin - offset)]
        left = self.left.move(self.left.end, self.left.end)
        right = self.right.move(self.right.begin, self.right.begin)
        super(SwapBrackets, self).run(edit, name)
        self.selection = selection
        self.left = left
        self.right = right
        self.nobracket = False


def plugin():
    return SwapBrackets
