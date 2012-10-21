import sublime
import os
from os.path import normpath, join, exists
import imp
from collections import namedtuple
import sys


class BracketRegion (namedtuple('BracketRegion', ['begin', 'end'], verbose=False)):
    def move(self, begin, end):
        return self._replace(begin=begin, end=end)

    def size(self):
        return abs(self.begin - self.end)


# Pull in built-in and custom plugin directory
BH_MODULES = os.path.join(sublime.packages_path(), 'BracketHighlighter')

if BH_MODULES not in sys.path:
    sys.path.append(BH_MODULES)


def is_bracket_region(obj):
    return isinstance(obj, BracketRegion)


class BracketPlugin(object):
    def __init__(self, plugin, loaded):
        self.enabled = False
        self.args = plugin['args'] if ("args" in plugin) else {}
        self.plugin = None
        if 'command' in plugin:
            plib = plugin['command']
            try:
                if plib.startswith("bh_modules"):
                    if "bh_modules" not in loaded:
                        imp.load_source("bh_modules", join(BH_MODULES, "bh_modules", "__init__.py"))
                        loaded.add("bh_modules")
                    path_name = join(BH_MODULES, normpath(plib.replace('.', '/')))
                else:
                    path_name = join(sublime.packages_path(), normpath(plib.replace('.', '/')))
                if not exists(path_name):
                    path_name += ".py"
                    assert exists(path_name)
                if plib in loaded:
                    module = sys.modules[plib]
                else:
                    module = imp.load_source(plib, path_name)
                self.plugin = getattr(module, 'plugin')()
                loaded.add(plib)
                self.enabled = True
            except Exception, e:
                print e
                sublime.error_message('Can not load plugin: ' + plugin['command'])

    def is_enabled(self):
        return self.enabled

    def run_command(self, view, name, left, right, selection):
        plugin = self.plugin()
        setattr(plugin, "left", left)
        setattr(plugin, "right", right)
        setattr(plugin, "view", view)
        setattr(plugin, "selection", selection)
        self.args["name"] = name
        plugin.run(**self.args)
        return plugin.left, plugin.right, plugin.selection


class BracketPluginCommand(object):
    def __setattr__(self, name, value):
        # if name in ["left", "right"] and not is_bracket_region(value):
        #     print type(value)
        #     raise TypeError
        super(BracketPluginCommand, self).__setattr__(name, value)

    def run(self, bracket, content, selection):
        pass
