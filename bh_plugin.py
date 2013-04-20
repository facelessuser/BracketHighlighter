import sublime
from os.path import normpath, join
import imp
from collections import namedtuple
import sys
import traceback
import warnings


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


def is_bracket_region(obj):
    """
    Check if object is a BracketRegion
    """

    return isinstance(obj, BracketRegion)


class ImportModule(object):
    @classmethod
    def import_module(cls, module_name, loaded=None):
        # Pull in built-in and custom plugin directory
        if module_name.startswith("bh_modules."):
            path_name = join(sublime.packages_path(), "BracketHighlighter", normpath(module_name.replace('.', '/')))
        else:
            path_name = join(sublime.packages_path(), normpath(module_name.replace('.', '/')))
        path_name += ".py"
        if loaded is not None and module_name in loaded:
            module = sys.modules[module_name]
        else:
            with warnings.catch_warnings(record=True) as w:
                # Ignore warnings about plugin folder not being a python package
                warnings.simplefilter("always")
                module = imp.new_module(module_name)
                sys.modules[module_name] = module
                source = None
                with open(path_name) as f:
                    source = f.read().replace('\r', '')
                cls.__execute_module(source, module_name)
                w = filter(lambda i: issubclass(i.category, UserWarning), w)
        return module

    @classmethod
    def __execute_module(cls, source, module_name):
        exec(compile(source, module_name, 'exec'), sys.modules[module_name].__dict__)

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
        setattr(plugin, "nobracket", False)
        edit = view.begin_edit()
        self.args["edit"] = edit
        self.args["name"] = name
        try:
            nobracket = False
            plugin.run(**self.args)
            left, right, selection, nobracket = plugin.left, plugin.right, plugin.selection, plugin.nobracket
        except Exception:
            print "BracketHighlighter: Plugin Run Error:\n%s" % str(traceback.format_exc())
        view.end_edit(edit)
        return left, right, selection, nobracket


class BracketPluginCommand(object):
    """
    Bracket Plugin base class
    """

    def run(self, bracket, content, selection):
        """
        Runs the plugin class
        """

        pass
