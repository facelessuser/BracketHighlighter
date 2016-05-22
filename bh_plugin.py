"""
BracketHighlighter.

Copyright (c) 2013 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import sublime
import sublime_plugin
from os.path import normpath, join
import imp
from collections import namedtuple
import sys
import traceback
import re
from BracketHighlighter.bh_logging import log


class Payload(object):
    """Plugin payload."""

    status = False
    plugin = None
    args = None

    @classmethod
    def clear(cls):
        """Clear payload."""

        cls.status = False
        cls.plugin = None
        cls.args = None


class BracketRegion (namedtuple('BracketRegion', ['begin', 'end'], verbose=False)):
    """Bracket Regions for plugins."""

    def move(self, begin, end):
        """Move bracket region to different points."""

        return self._replace(begin=begin, end=end)

    def size(self):
        """Get the size of the region."""

        return abs(self.begin - self.end)

    def toregion(self):
        """Convert to sublime region."""

        return sublime.Region(self.begin, self.end)


def is_bracket_region(obj):
    """Check if object is a BracketRegion."""

    return isinstance(obj, BracketRegion)


def sublime_format_path(pth):
    """Format path for Sublime internally."""
    m = re.match(r"^([A-Za-z]{1}):(?:/|\\)(.*)", pth)
    if sublime.platform() == "windows" and m is not None:
        pth = m.group(1) + "/" + m.group(2)
    return pth.replace("\\", "/")


def load_modules(obj, loaded):
    """Load bracket plugin modules."""

    plib = obj.get("plugin_library")
    if plib is None:
        return

    try:
        module = _import_module(plib, loaded)
        obj["compare"] = getattr(module, "compare", None)
        obj["post_match"] = getattr(module, "post_match", None)
        obj["validate"] = getattr(module, "validate", None)
        obj["highlighting"] = getattr(module, "highlighting", None)
        loaded.add(plib)
    except Exception:
        log("Could not load module %s\n%s" % (plib, str(traceback.format_exc())))
        raise


def _import_module(module_name, loaded=None):
    """
    Import the module.

    Import the module and track which modules have been loaded
    so we don't load already loaded modules.
    """

    # Pull in built-in and custom plugin directory
    if module_name.startswith("bh_modules."):
        path_name = join("Packages", "BracketHighlighter", normpath(module_name.replace('.', '/')))
    else:
        path_name = join("Packages", normpath(module_name.replace('.', '/')))
    path_name += ".py"
    if loaded is not None and module_name in loaded:
        module = sys.modules[module_name]
    else:
        module = imp.new_module(module_name)
        sys.modules[module_name] = module
        exec(
            compile(
                sublime.load_resource(sublime_format_path(path_name)),
                module_name,
                'exec'
            ),
            sys.modules[module_name].__dict__
        )
    return module


def import_module(module, attribute=None):
    """Import module or module attribute."""

    mod = _import_module(module)
    return getattr(mod, attribute) if attribute is not None else mod


class BracketPluginRunCommand(sublime_plugin.TextCommand):
    """Sublime run command to run BH plugins."""

    def run(self, edit):
        """Run the plugin."""

        try:
            Payload.args["edit"] = edit
            Payload.plugin.run(**Payload.args)
            Payload.status = True
        except Exception:
            print("BracketHighlighter: Plugin Run Error:\n%s" % str(traceback.format_exc()))


class BracketPlugin(object):
    """Class for preparing and running plugins."""

    def __init__(self, plugin, loaded):
        """Load plugin module."""

        self.enabled = False
        self.args = plugin['args'] if ("args" in plugin) else {}
        self.plugin = None
        if 'command' in plugin:
            plib = plugin['command']
            try:
                module = _import_module(plib, loaded)
                self.plugin = getattr(module, 'plugin')()
                loaded.add(plib)
                self.enabled = True
            except Exception:
                print('BracketHighlighter: Load Plugin Error: %s\n%s' % (plugin['command'], traceback.format_exc()))

    def is_enabled(self):
        """Check if plugin is enabled."""

        return self.enabled

    def run_command(self, view, name, left, right, selection):
        """Load arguments into plugin and run."""

        nobracket = False
        refresh_match = False
        Payload.status = False
        Payload.plugin = self.plugin()
        setattr(Payload.plugin, "left", left)
        setattr(Payload.plugin, "right", right)
        setattr(Payload.plugin, "view", view)
        setattr(Payload.plugin, "selection", selection)
        setattr(Payload.plugin, "nobracket", False)
        setattr(Payload.plugin, "refresh_match", False)
        self.args["edit"] = None
        self.args["name"] = name
        Payload.args = self.args

        # Call a TextCommand to run the plugin so it can feed in the Edit object
        view.run_command("bracket_plugin_run")

        if Payload.status:
            left = Payload.plugin.left
            right = Payload.plugin.right
            selection = Payload.plugin.selection
            nobracket = Payload.plugin.nobracket
            refresh_match = Payload.plugin.refresh_match
        Payload.clear()

        return left, right, selection, nobracket, refresh_match


class BracketPluginCommand(object):
    """Bracket Plugin base class."""

    def run(self, bracket, content, selection):
        """Run the plugin class."""

        pass
