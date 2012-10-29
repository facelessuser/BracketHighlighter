import bh_plugin


class SelectAttr(bh_plugin.BracketPluginCommand):
    def run(self, edit, name, direction='right'):
        if self.left.size() <= 1:
            return
        tag_name = r'[\w\:\-]+'
        attr_name = r'''([\w\-\.:]+)(?:\s*=\s*(?:(?:"((?:\.|[^"])*)")|(?:'((?:\.|[^'])*)')|([^>\s]+)))?'''
        tname = self.view.find(tag_name, self.left.begin)
        current = self.selection[0].b
        region = self.view.find(attr_name, tname.b)
        selection = self.selection

        if direction == 'left':
            last = None

            # Keep track of last attr
            if region != None and current <= region.b and region.b < self.left.end:
                last = region

            while region != None and region.b < self.left.end:
                # Select attribute until you have closest to the left of selection
                if current > region.b:
                    selection = [region]
                    last = None
                # Update last attr
                elif last != None:
                    last = region
                region = self.view.find(attr_name, region.b)
            # Wrap right
            if last != None:
                selection = [last]
        else:
            first = None
            # Keep track of first attr
            if region != None and region.b < self.left.end:
                first = region

            while region != None and region.b < self.left.end:
                # Select closest attr to the right of the selection
                if current < region.b:
                    selection = [region]
                    first = None
                    break
                region = self.view.find(attr_name, region.b)
            # Wrap left
            if first != None:
                selection = [first]
        self.selection = selection


def plugin():
    return SelectAttr
