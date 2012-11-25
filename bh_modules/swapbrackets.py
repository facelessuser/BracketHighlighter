import sublime
from bh_plugin import ImportModule as ImpMod
BracketRemove = ImpMod.import_from("bh_modules.bracketremove", "BracketRemove")


class SwapBrackets(BracketRemove):
    def run(self, edit, name, remove_content=False, remove_indent=False, remove_block=False):
        offset = self.left.toregion().size()
        self.selection = [sublime.Region(self.left.begin, self.right.begin - offset)]
        super(SwapBrackets, self).run(edit, name)


def plugin():
    return SwapBrackets
