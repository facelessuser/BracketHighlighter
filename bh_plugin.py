import sublime
import os
from os.path import normpath, join, exists
import imp
from collections import namedtuple
import sys
import traceback


class BracketRegion (namedtuple('BracketRegion', ['begin', 'end'], verbose=False)):
    """
    Bracket Regions for plugins
    """

    def move(self, begin, end):
        """
        Move bracket region to different points
        """

        return self._replace(begin=begin, end=end)

    def size(self):
        """
        Get the size of the region
        """

        return abs(self.begin - self.end)

    def toregion(self):
        """
        Convert to sublime region
        """

        return sublime.Region(self.begin, self.end)


# Pull in built-in and custom plugin directory
BH_MODULES = os.path.join(sublime.packages_path(), 'BracketHighlighter')

if BH_MODULES not in sys.path:
    sys.path.append(BH_MODULES)


def is_bracket_region(obj):
    """
    Check if object is a BracketRegion
    """

    return isinstance(obj, BracketRegion)


class ImportModule(object):
    @classmethod
    def import_module(cls, module_name, loaded=None):
        if module_name.startswith("bh_modules."):
            path_name = join(BH_MODULES, normpath(module_name.replace('.', '/')))
            module_name = module_name.replace("bh_modules.", "")
        else:
            path_name = join(sublime.packages_path(), normpath(module_name.replace('.', '/')))
        if not exists(path_name):
            path_name += ".py"
            assert exists(path_name)
        if loaded is not None and module_name in loaded:
            module = sys.modules[module_name]
        else:
            module = imp.load_source(module_name, path_name)
        return module

    @classmethod
    def import_from(cls, module_name, attribute):
        return getattr(cls.import_module(module_name), attribute)


class BracketPlugin(object):
    """
    Class for preparing and running plugins
    """

    def __init__(self, plugin, loaded):
        """
        Load plugin module
        """

        self.enabled = False
        self.args = plugin['args'] if ("args" in plugin) else {}
        self.plugin = None
        if 'command' in plugin:
            plib = plugin['command']
            try:
                module = ImportModule.import_module(plib, loaded)
                self.plugin = getattr(module, 'plugin')()
                loaded.add(plib)
                self.enabled = True
            except Exception:
                print 'BracketHighlighter: Load Plugin Error: %s\n%s' % (plugin['command'], traceback.format_exc())

    def is_enabled(self):
        """
        Check if plugin is enabled
        """

        return self.enabled

    def run_command(self, view, name, left, right, selection):
        """
        Load arguments into plugin and run
        """

        plugin = self.plugin()
        setattr(plugin, "left", left)
        setattr(plugin, "right", right)
        setattr(plugin, "view", view)
        setattr(plugin, "selection", selection)
        edit = view.begin_edit()
        self.args["edit"] = edit
        self.args["name"] = name
        try:
            plugin.run(**self.args)
            left, right, selection = plugin.left, plugin.right, plugin.selection
        except Exception:
            print "BracketHighlighter: Plugin Run Error:\n%s" % str(traceback.format_exc())
        view.end_edit(edit)
        return left, right, selection


class BracketPluginCommand(object):
    """
    Bracket Plugin base class
    """

    def run(self, bracket, content, selection):
        """
        Runs the plugin class
        """

        pass
