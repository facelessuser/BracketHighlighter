import bh_plugin


class TagNameSelect(bh_plugin.BracketPluginCommand):
    def run(self, edit, name):
        if self.left.size() > 1:
            tag_name = '[\w\:\-]+'
            region1 = self.view.find(tag_name, self.left.begin)
            region2 = self.view.find(tag_name, self.right.begin)
            self.selection = [region1, region2]


def plugin():
    return TagNameSelect
