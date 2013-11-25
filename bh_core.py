from os.path import basename, exists, join, normpath
import sublime
import sublime_plugin
from time import time, sleep
import thread
import ure
from bh_plugin import BracketPlugin, BracketRegion, ImportModule
from collections import namedtuple
import traceback

ure.set_cache_directory(join(sublime.packages_path(), "User"), "bh")

BH_MATCH_TYPE_NONE = 0
BH_MATCH_TYPE_SELECTION = 1
BH_MATCH_TYPE_EDIT = 2
DEFAULT_STYLES = {
    "default": {
        "icon": "dot",
        "color": "brackethighlighter.default",
        "style": "underline"
    },
    "unmatched": {
        "icon": "question",
        "color": "brackethighlighter.unmatched",
        "style": "outline"
    }
}
HV_RSVD_VALUES = ["__default__", "__bracket__"]

HIGH_VISIBILITY = False

GLOBAL_ENABLE = True


def bh_logging(msg):
    print("BracketHighlighter: %s" % msg)


def bh_debug(msg):
    if sublime.load_settings("bh_core.sublime-settings").get('debug_enable', False):
        bh_logging(msg)


def underline(regions):
    """
    Convert sublime regions into underline regions
    """

    r = []
    for region in regions:
        start = region.begin()
        end = region.end()
        while start < end:
            r.append(sublime.Region(start))
            start += 1
    return r


def load_modules(obj, loaded):
    """
    Load bracket plugin modules
    """

    plib = obj.get("plugin_library")
    if plib is None:
        return

    try:
        module = ImportModule.import_module(plib, loaded)
        obj["compare"] = getattr(module, "compare", None)
        obj["post_match"] = getattr(module, "post_match", None)
        loaded.add(plib)
    except:
        bh_logging("Could not load module %s\n%s" % (plib, str(traceback.format_exc())))
        raise


def select_bracket_style(option):
    """
    Configure style of region based on option
    """

    style = sublime.HIDE_ON_MINIMAP
    if option == "outline":
        style |= sublime.DRAW_OUTLINED
    elif option == "none":
        style |= sublime.HIDDEN
    elif option == "underline":
        style |= sublime.DRAW_EMPTY_AS_OVERWRITE
    return style


def select_bracket_icons(option, icon_path):
    """
    Configure custom gutter icons if they can be located.
    """

    icon = ""
    small_icon = ""
    open_icon = ""
    small_open_icon = ""
    close_icon = ""
    small_close_icon = ""
    # Icon exist?
    if not option == "none" and not option == "":
        if exists(normpath(join(sublime.packages_path(), icon_path, option + ".png"))):
            icon = "../%s/%s" % (icon_path, option)
        if exists(normpath(join(sublime.packages_path(), icon_path, option + "_small.png"))):
            small_icon = "../%s/%s" % (icon_path, option + "_small")
        if exists(normpath(join(sublime.packages_path(), icon_path, option + "_open.png"))):
            open_icon = "../%s/%s" % (icon_path, option + "_open")
        else:
            open_icon = icon
        if exists(normpath(join(sublime.packages_path(), icon_path, option + "_open_small.png"))):
            small_open_icon = "../%s/%s" % (icon_path, option + "_open_small")
        else:
            small_open_icon = small_icon
        if exists(normpath(join(sublime.packages_path(), icon_path, option + "_close.png"))):
            close_icon = "../%s/%s" % (icon_path, option + "_close")
        else:
            close_icon = icon
        if exists(normpath(join(sublime.packages_path(), icon_path, option + "_close_small.png"))):
            small_close_icon = "../%s/%s" % (icon_path, option + "_close_small")
        else:
            small_close_icon = small_icon

    return icon, small_icon, open_icon, small_open_icon, close_icon, small_close_icon


def exclude_bracket(enabled, filter_type, language_list, language):
    """
    Exclude or include brackets based on filter lists.
    """

    exclude = True
    if enabled:
        # Black list languages
        if filter_type == 'blacklist':
            exclude = False
            if language != None:
                for item in language_list:
                    if language == item.lower():
                        exclude = True
                        break
        #White list languages
        elif filter_type == 'whitelist':
            if language != None:
                for item in language_list:
                    if language == item.lower():
                        exclude = False
                        break
    return exclude


class BhEventMgr(object):
    """
    Object to manage when bracket events should be launched.
    """

    @classmethod
    def load(cls):
        """
        Initialize variables for determining
        when to initiate a bracket matching event.
        """

        cls.wait_time = 0.12
        cls.time = time()
        cls.modified = False
        cls.type = BH_MATCH_TYPE_SELECTION
        cls.ignore_all = False

BhEventMgr.load()


class BhThreadMgr(object):
    """
    Object to help track when a new thread needs to be started.
    """

    restart = False


class BhEntry(object):
    """
    Generic object for bracket regions.
    """

    def move(self, begin, end):
        """
        Create a new object with the points moved to the specified locations.
        """

        return self._replace(begin=begin, end=end)

    def size(self):
        """
        Size of bracket selection.
        """

        return abs(self.begin - self.end)

    def toregion(self):
        """
        Convert to sublime Region.
        """

        return sublime.Region(self.begin, self.end)


class BracketEntry(namedtuple('BracketEntry', ['begin', 'end', 'type'], verbose=False), BhEntry):
    """
    Bracket object.
    """

    pass


class ScopeEntry(namedtuple('ScopeEntry', ['begin', 'end', 'scope', 'type'], verbose=False), BhEntry):
    """
    Scope bracket object.
    """

    pass


class BracketSearchSide(object):
    """
    Userful structure to specify bracket matching direction.
    """

    left = 0
    right = 1


class BracektSearchType(object):
    """
    Userful structure to specify bracket matching direction.
    """

    opening = 0
    closing = 1


class BracketSearch(object):
    """
    Object that performs regex search on the view's buffer and finds brackets.
    """

    def __init__(self, bfr, window, center, pattern, scope_check, scope):
        """
        Prepare the search object
        """

        self.center = center
        self.pattern = pattern
        self.bfr = bfr
        self.scope = scope
        self.scope_check = scope_check
        self.prev_match = [None, None]
        self.return_prev = [False, False]
        self.done = [False, False]
        self.start = [None, None]
        self.left = [[], []]
        self.right = [[], []]
        self.findall(window)

    def reset_end_state(self):
        """
        Reset the the current search flags etc.
        This is usually done before searching the other direction.
        """

        self.start = [None, None]
        self.done = [False, False]
        self.prev_match = [None, None]
        self.return_prev = [False, False]

    def remember(self, match_type):
        """
        Remember the current match.
        Don't get the next bracket on the next
        request, but return the current one again.
        """

        self.return_prev[match_type] = True
        self.done[match_type] = False

    def findall(self, window):
        """
        Find all of the brackets and sort them
        to "left of the cursor" and "right of the cursor"
        """

        for m in self.pattern.finditer(self.bfr, window[0], window[1]):
            g = m.lastindex
            try:
                start = m.start(g)
                end = m.end(g)
            except:
                continue

            match_type = int(not bool(g % 2))
            bracket_id = (g / 2) - match_type

            if not self.scope_check(start, bracket_id, self.scope):
                if (end <= self.center if match_type else start < self.center):
                    self.left[match_type].append(BracketEntry(start, end, bracket_id))
                elif (end > self.center if match_type else start >= self.center):
                    self.right[match_type].append(BracketEntry(start, end, bracket_id))

    def get_open(self, bracket_code):
        """
        Get opening bracket.  Accepts a bracket code that
        determines which side of the cursor the next match is returned from.
        """

        for b in self._get_bracket(bracket_code, BracektSearchType.opening):
            yield b

    def get_close(self, bracket_code):
        """
        Get closing bracket.  Accepts a bracket code that
        determines which side of the cursor the next match is returned from.
        """

        for b in self._get_bracket(bracket_code, BracektSearchType.closing):
            yield b

    def is_done(self, match_type):
        """
        Retrieve done flag.
        """

        return self.done[match_type]

    def _get_bracket(self, bracket_code, match_type):
        """
        Get the next bracket.  Accepts bracket code that determines
        which side of the cursor the next match is returned from and
        the match type which determines whether a opening or closing
        bracket is desired.
        """

        if self.done[match_type]:
            return
        if self.return_prev[match_type]:
            self.return_prev[match_type] = False
            yield self.prev_match[match_type]
        if bracket_code == BracketSearchSide.left:
            if self.start[match_type] is None:
                self.start[match_type] = len(self.left[match_type])
            for x in reversed(range(0, self.start[match_type])):
                b = self.left[match_type][x]
                self.prev_match[match_type] = b
                self.start[match_type] -= 1
                yield b
        else:
            if self.start[match_type] is None:
                self.start[match_type] = 0
            for x in range(self.start[match_type], len(self.right[match_type])):
                b = self.right[match_type][x]
                self.prev_match[match_type] = b
                self.start[match_type] += 1
                yield b

        self.done[match_type] = True


class BracketDefinition(object):
    """
    Normal bracket definition.
    """

    def __init__(self, bracket):
        """
        Setup the bracket object by reading the passed in dictionary.
        """

        self.name = bracket["name"]
        self.style = bracket.get("style", "default")
        self.compare = bracket.get("compare")
        sub_search = bracket.get("find_in_sub_search", "false")
        self.find_in_sub_search_only = sub_search == "only"
        self.find_in_sub_search = sub_search == "true" or self.find_in_sub_search_only
        self.post_match = bracket.get("post_match")
        self.scope_exclude_exceptions = bracket.get("scope_exclude_exceptions", [])
        self.scope_exclude = bracket.get("scope_exclude", [])
        self.ignore_string_escape = bracket.get("ignore_string_escape", False)


class ScopeDefinition(object):
    """
    Scope bracket definition.
    """

    def __init__(self, bracket):
        """
        Setup the bracket object by reading the passed in dictionary.
        """

        self.style = bracket.get("style", "default")
        self.open = ure.compile("\\A" + bracket.get("open", "."), ure.MULTILINE | ure.IGNORECASE)
        self.close = ure.compile(bracket.get("close", ".") + "\\Z", ure.MULTILINE | ure.IGNORECASE)
        self.name = bracket["name"]
        sub_search = bracket.get("sub_bracket_search", "false")
        self.sub_search_only = sub_search == "only"
        self.sub_search = self.sub_search_only == True or sub_search == "true"
        self.compare = bracket.get("compare")
        self.post_match = bracket.get("post_match")
        self.scopes = bracket["scopes"]


class StyleDefinition(object):
    """
    Styling definition.
    """

    def __init__(self, name, style, default_highlight, icon_path):
        """
        Setup the style object by reading the
        passed in dictionary. And other parameters.
        """

        self.name = name
        self.selections = []
        self.open_selections = []
        self.close_selections = []
        self.center_selections = []
        self.color = style.get("color", default_highlight["color"])
        self.style = select_bracket_style(style.get("style", default_highlight["style"]))
        self.underline = self.style & sublime.DRAW_EMPTY_AS_OVERWRITE
        (
            self.icon, self.small_icon, self.open_icon,
            self.small_open_icon, self.close_icon, self.small_close_icon
        ) = select_bracket_icons(style.get("icon", default_highlight["icon"]), icon_path)
        self.no_icon = ""


class BhToggleStringEscapeModeCommand(sublime_plugin.TextCommand):
    """
    Toggle between regex escape and
    string escape for brackets in strings.
    """

    def run(self, edit):
        default_mode = sublime.load_settings("bh_core.sublime-settings").get('bracket_string_escape_mode', 'string')
        if self.view.settings().get('bracket_string_escape_mode', default_mode) == "regex":
            self.view.settings().set('bracket_string_escape_mode', "string")
            sublime.status_message("Bracket String Escape Mode: string")
        else:
            self.view.settings().set('bracket_string_escape_mode', "regex")
            sublime.status_message("Bracket String Escape Mode: regex")


class BhShowStringEscapeModeCommand(sublime_plugin.TextCommand):
    """
    Shoe current string escape mode for sub brackets in strings.
    """

    def run(self, edit):
        default_mode = sublime.load_settings("BracketHighlighter.sublime-settings").get('bracket_string_escape_mode', 'string')
        sublime.status_message("Bracket String Escape Mode: %s" % self.view.settings().get('bracket_string_escape_mode', default_mode))


class BhToggleHighVisibilityCommand(sublime_plugin.ApplicationCommand):
    """
    Toggle a high visibility mode that
    highlights the entire bracket extent.
    """

    def run(self):
        global HIGH_VISIBILITY
        HIGH_VISIBILITY = not HIGH_VISIBILITY


class BhToggleEnableCommand(sublime_plugin.ApplicationCommand):
    """
    Toggle global enable for BracketHighlighter.
    """

    def run(self):
        global GLOBAL_ENABLE
        GLOBAL_ENABLE = not GLOBAL_ENABLE


class BhKeyCommand(sublime_plugin.WindowCommand):
    """
    Command to process shortcuts, menu calls, and command palette calls.
    This is how BhCore is called with different options.
    """

    def run(self, threshold=True, lines=False, adjacent=False, ignore={}, plugin={}):
        # Override events
        BhEventMgr.ignore_all = True
        BhEventMgr.modified = False
        self.bh = BhCore(
            threshold,
            lines,
            adjacent,
            ignore,
            plugin,
            True
        )
        self.view = self.window.active_view()
        sublime.set_timeout(self.execute, 100)

    def execute(self):
        bh_debug("Key Event")
        self.bh.match(self.view)
        BhEventMgr.ignore_all = False
        BhEventMgr.time = time()


class BhCore(object):
    """
    Bracket matching class.
    """
    plugin_reload = False

    def __init__(self, override_thresh=False, count_lines=False, adj_only=None, ignore={}, plugin={}, keycommand=False):
        """
        Load settings and setup reload events if settings changes.
        """

        self.settings = sublime.load_settings("bh_core.sublime-settings")
        self.keycommand = keycommand
        if not keycommand:
            self.settings.clear_on_change('reload')
            self.settings.add_on_change('reload', self.setup)
        self.setup(override_thresh, count_lines, adj_only, ignore, plugin)

    def setup(self, override_thresh=False, count_lines=False, adj_only=None, ignore={}, plugin={}):
        """
        Initialize class settings from settings file and inputs.
        """

        # Init view params
        self.last_id_view = None
        self.last_id_sel = None
        self.view_tracker = (None, None)
        self.ignore_threshold = override_thresh or bool(self.settings.get("ignore_threshold", False))
        self.adj_only = adj_only if adj_only is not None else bool(self.settings.get("match_only_adjacent", False))
        self.auto_selection_threshold = int(self.settings.get("auto_selection_threshold", 10))
        self.no_multi_select_icons = bool(self.settings.get("no_multi_select_icons", False))
        self.count_lines = count_lines
        self.default_string_escape_mode = str(self.settings.get('bracket_string_escape_mode', "string"))

        # Init bracket objects
        self.bracket_types = self.settings.get("brackets", [])
        self.scope_types = self.settings.get("scope_brackets", [])

        # Init selection params
        self.use_selection_threshold = True
        self.selection_threshold = int(self.settings.get("search_threshold", 5000))
        self.new_select = False
        self.loaded_modules = set([])

        # High Visibility options
        self.hv_style = select_bracket_style(self.settings.get("high_visibility_style", "outline"))
        self.hv_underline = self.hv_style & sublime.DRAW_EMPTY_AS_OVERWRITE
        self.hv_color = self.settings.get("high_visibility_color", HV_RSVD_VALUES[1])

        # Init plugin
        self.plugin = None
        self.transform = set([])
        if 'command' in plugin:
            self.plugin = BracketPlugin(plugin, self.loaded_modules)
            self.new_select = True
            if 'type' in plugin:
                for t in plugin["type"]:
                    self.transform.add(t)

    def eval_show_unmatched(self, show_unmatched, exception, language):
        """
        Determine if show_unmatched should be enabled for the current view
        """
        answer = True
        if show_unmatched is True or show_unmatched is False:
            answer = show_unmatched
        if isinstance(exception, list):
            for option in exception:
                if option.lower() == language:
                    answer = not answer
                    break
        return answer

    def init_bracket_regions(self):
        """
        Load up styled regions for brackets to use.
        """

        self.bracket_regions = {}
        styles = self.settings.get("bracket_styles", DEFAULT_STYLES)
        icon_path = self.settings.get("icon_path", "Theme - Default").replace('\\', '/').strip('/')
        # Make sure default and unmatched styles in styles
        for key, value in DEFAULT_STYLES.items():
            if key not in styles:
                styles[key] = value
                continue
            for k, v in value.items():
                if k not in styles[key]:
                    styles[key][k] = v
        # Initialize styles
        default_settings = styles["default"]
        for k, v in styles.items():
            self.bracket_regions[k] = StyleDefinition(k, v, default_settings, icon_path)

    def is_valid_definition(self, params, language):
        """
        Ensure bracket definition should be and can be loaded.
        """

        return (
            not exclude_bracket(
                params.get("enabled", True),
                params.get("language_filter", "blacklist"),
                params.get("language_list", []),
                language
            ) and
            params["open"] is not None and params["close"] is not None
        )

    def init_brackets(self, language):
        """
        Initialize bracket match definition objects from settings file.
        """

        self.find_regex = []
        self.sub_find_regex = []
        self.index_open = {}
        self.index_close = {}
        self.brackets = []
        self.scopes = []
        self.view_tracker = (language, self.view.id())
        self.enabled = False
        self.sels = []
        self.multi_select = False
        scopes = {}
        loaded_modules = self.loaded_modules.copy()

        for params in self.bracket_types:
            if self.is_valid_definition(params, language):
                try:
                    load_modules(params, loaded_modules)
                    entry = BracketDefinition(params)
                    self.brackets.append(entry)
                    if not entry.find_in_sub_search_only:
                        self.find_regex.append(params["open"])
                        self.find_regex.append(params["close"])
                    else:
                        self.find_regex.append(r"([^\s\S])")
                        self.find_regex.append(r"([^\s\S])")

                    if entry.find_in_sub_search:
                        self.sub_find_regex.append(params["open"])
                        self.sub_find_regex.append(params["close"])
                    else:
                        self.sub_find_regex.append(r"([^\s\S])")
                        self.sub_find_regex.append(r"([^\s\S])")
                except Exception, e:
                    bh_logging(e)

        scope_count = 0
        for params in self.scope_types:
            if self.is_valid_definition(params, language):
                try:
                    load_modules(params, loaded_modules)
                    entry = ScopeDefinition(params)
                    for x in entry.scopes:
                        if x not in scopes:
                            scopes[x] = scope_count
                            scope_count += 1
                            self.scopes.append({"name": x, "brackets": [entry]})
                        else:
                            self.scopes[scopes[x]]["brackets"].append(entry)
                except Exception, e:
                    bh_logging(e)

        if len(self.brackets):
            bh_debug(
                "Search patterns:\n" +
                "(?:%s)\n" % '|'.join(self.find_regex) +
                "(?:%s)" % '|'.join(self.sub_find_regex)
            )
            self.sub_pattern = ure.compile("(?:%s)" % '|'.join(self.sub_find_regex), ure.MULTILINE | ure.IGNORECASE)
            self.pattern = ure.compile("(?:%s)" % '|'.join(self.find_regex), ure.MULTILINE | ure.IGNORECASE)
            self.enabled = True

    def init_match(self):
        """
        Initialize matching for the current view's syntax.
        """

        self.chars = 0
        self.lines = 0
        syntax = self.view.settings().get('syntax')
        language = basename(syntax).replace('.tmLanguage', '').lower() if syntax != None else "plain text"
        show_unmatched = self.settings.get("show_unmatched", True),
        show_unmatched_exceptions = self.settings.get("show_unmatched_exceptions", [])

        if language != self.view_tracker[0] or self.view.id() != self.view_tracker[1]:
            self.init_bracket_regions()
            self.init_brackets(language)
            self.show_unmatched = self.eval_show_unmatched(show_unmatched, show_unmatched_exceptions, language)
        else:
            for r in self.bracket_regions.values():
                r.selections = []
                r.open_selections = []
                r.close_selections = []
                r.center_selections = []

    def unique(self):
        """
        Check if the current selection(s) is different from the last.
        """

        id_view = self.view.id()
        id_sel = "".join([str(sel.a) for sel in self.view.sel()])
        is_unique = False
        if id_view != self.last_id_view or id_sel != self.last_id_sel:
            self.last_id_view = id_view
            self.last_id_sel = id_sel
            is_unique = True
        return is_unique

    def store_sel(self, regions):
        """
        Store the current selection selection to be set at the end.
        """

        if self.new_select:
            for region in regions:
                self.sels.append(region)

    def change_sel(self):
        """
        Change the view's selections.
        """

        if self.new_select and len(self.sels) > 0:
            if self.multi_select == False:
                self.view.show(self.sels[0])
            self.view.sel().clear()
            map(lambda x: self.view.sel().add(x), self.sels)

    def hv_highlight_color(self, b_value):
        """
        High visibility highlight decesions.
        """

        color = self.hv_color
        if self.hv_color == HV_RSVD_VALUES[0]:
            color = self.bracket_regions["default"].color
        elif self.hv_color == HV_RSVD_VALUES[1]:
            color = b_value
        return color

    def highlight_regions(self, name, icon_type, selections, bracket, regions):
        """
        Apply the highlightes for the highlight region.
        """

        if len(selections):
            self.view.add_regions(
                name,
                getattr(bracket, selections),
                self.hv_highlight_color(bracket.color) if HIGH_VISIBILITY else bracket.color,
                getattr(bracket, icon_type),
                self.hv_style if HIGH_VISIBILITY else bracket.style
            )
            regions.append(name)

    def highlight(self, view):
        """
        Highlight all bracket regions.
        """

        for region_key in self.view.settings().get("bh_regions", []):
            self.view.erase_regions(region_key)

        regions = []
        icon_type = "no_icon"
        open_icon_type = "no_icon"
        close_icon_type = "no_icon"
        if not self.no_multi_select_icons or not self.multi_select:
            icon_type = "small_icon" if self.view.line_height() < 16 else "icon"
            open_icon_type = "small_open_icon" if self.view.line_height() < 16 else "open_icon"
            close_icon_type = "small_close_icon" if self.view.line_height() < 16 else "close_icon"
        for name, r in self.bracket_regions.items():
            self.highlight_regions("bh_" + name, icon_type, "selections", r, regions)
            self.highlight_regions("bh_" + name + "_center", "no_icon", "center_selections", r, regions)
            self.highlight_regions("bh_" + name + "_open", open_icon_type, "open_selections", r, regions)
            self.highlight_regions("bh_" + name + "_close", close_icon_type, "close_selections", r, regions)
        # Track which regions were set in the view so that they can be cleaned up later.
        self.view.settings().set("bh_regions", regions)

    def get_search_bfr(self, sel):
        """
        Read in the view's buffer for scanning for brackets etc.
        """

        # Determine how much of the buffer to search
        view_min = 0
        view_max = self.view.size()
        if not self.ignore_threshold:
            left_delta = sel.a - view_min
            right_delta = view_max - sel.a
            limit = self.selection_threshold / 2
            rpad = limit - left_delta if left_delta < limit else 0
            lpad = limit - right_delta if right_delta < limit else 0
            llimit = limit + lpad
            rlimit = limit + rpad
            self.search_window = (
                sel.a - llimit if left_delta >= llimit else view_min,
                sel.a + rlimit if right_delta >= rlimit else view_max
            )
        else:
            self.search_window = (0, view_max)

        # Search Buffer
        return self.view.substr(sublime.Region(0, view_max))

    def match(self, view, force_match=True):
        """
        Preform matching brackets surround the selection(s)
        """

        if view == None:
            return

        view.settings().set("BracketHighlighterBusy", True)

        if not GLOBAL_ENABLE:
            for region_key in view.settings().get("bh_regions", []):
                view.erase_regions(region_key)
            view.settings().set("BracketHighlighterBusy", False)
            return

        if self.keycommand:
            BhCore.plugin_reload = True

        if not self.keycommand and BhCore.plugin_reload:
            self.setup()
            BhCore.plugin_reload = False

        # Setup views
        self.view = view
        self.last_view = view
        num_sels = len(view.sel())
        self.multi_select = (num_sels > 1)

        if self.unique() or force_match:
            # Initialize
            self.init_match()

            # Nothing to search for
            if not self.enabled:
                view.settings().set("BracketHighlighterBusy", False)
                return

            # Abort if selections are beyond the threshold
            if self.use_selection_threshold and num_sels >= self.selection_threshold:
                self.highlight(view)
                view.settings().set("BracketHighlighterBusy", False)
                return

            multi_select_count = 0
            # Process selections.
            for sel in view.sel():
                bfr = self.get_search_bfr(sel)
                if not self.ignore_threshold and multi_select_count >= self.auto_selection_threshold:
                    self.store_sel([sel])
                    multi_select_count += 1
                    continue
                if not self.find_scopes(bfr, sel):
                    self.sub_search_mode = False
                    self.find_matches(bfr, sel)
                multi_select_count += 1

        # Highlight, focus, and display lines etc.
        self.change_sel()
        self.highlight(view)
        if self.count_lines:
            sublime.status_message('In Block: Lines ' + str(self.lines) + ', Chars ' + str(self.chars))
        view.settings().set("BracketHighlighterBusy", False)

    def save_incomplete_regions(self, left, right, regions):
        """
        Store single incomplete brackets for highlighting.
        """

        found = left if left is not None else right
        bracket = self.bracket_regions["unmatched"]
        if bracket.underline:
            bracket.selections += underline((found.toregion(),))
        else:
            bracket.selections += [found.toregion()]
        self.store_sel(regions)

    def save_regions(self, left, right, regions):
        """
        Saved matched regions.  Perform any special considerations for region formatting.
        """

        bracket = self.bracket_regions.get(self.bracket_style, self.bracket_regions["default"])
        lines = abs(self.view.rowcol(right.begin)[0] - self.view.rowcol(left.end)[0] + 1)
        if self.count_lines:
            self.chars += abs(right.begin - left.end)
            self.lines += lines
        if HIGH_VISIBILITY:
            if lines <= 1:
                if self.hv_underline:
                    bracket.selections += underline((sublime.Region(left.begin, right.end),))
                else:
                    bracket.selections += [sublime.Region(left.begin, right.end)]
            else:
                bracket.open_selections += [sublime.Region(left.begin)]
                if self.hv_underline:
                    bracket.center_selections += underline((sublime.Region(left.begin + 1, right.end - 1),))
                else:
                    bracket.center_selections += [sublime.Region(left.begin, right.end)]
                bracket.close_selections += [sublime.Region(right.begin)]
        elif bracket.underline:
            if lines <= 1:
                bracket.selections += underline((left.toregion(), right.toregion()))
            else:
                bracket.open_selections += [sublime.Region(left.begin)]
                bracket.close_selections += [sublime.Region(right.begin)]
                if left.size():
                    bracket.center_selections += underline((sublime.Region(left.begin + 1, left.end),))
                if right.size():
                    bracket.center_selections += underline((sublime.Region(right.begin + 1, right.end),))
        else:
            if lines <= 1:
                bracket.selections += [left.toregion(), right.toregion()]
            else:
                bracket.open_selections += [left.toregion()]
                bracket.close_selections += [right.toregion()]
        self.store_sel(regions)

    def sub_search(self, sel, search_window, bfr, scope=None):
        """
        Search a scope bracket match for bracekts within.
        """

        bracket = None
        left, right = self.match_brackets(bfr, search_window, sel, scope)

        regions = [sublime.Region(sel.a, sel.b)]

        if left is not None and right is not None:
            bracket = self.brackets[left.type]
            left, right, regions, nobracket = self.run_plugin(bracket.name, left, right, regions)
            if nobracket:
                return True

        # Matched brackets
        if left is not None and right is not None and bracket is not None:
            self.save_regions(left, right, regions)
            return True
        return False

    def find_scopes(self, bfr, sel):
        """
        Find brackets by scope definition.
        """

        # Search buffer
        left, right, bracket, sub_matched = self.match_scope_brackets(bfr, sel)
        if sub_matched:
            return True
        regions = [sublime.Region(sel.a, sel.b)]

        if left is not None and right is not None:
            left, right, regions, _ = self.run_plugin(bracket.name, left, right, regions)
            if left is None and right is None:
                self.store_sel(regions)
                return True

        if left is not None and right is not None:
            self.save_regions(left, right, regions)
            return True
        elif (left is not None or right is not None) and self.show_invalid:
            self.save_incomplete_regions(left, right, regions)
            return True
        return False

    def find_matches(self, bfr, sel):
        """
        Find bracket matches
        """

        bracket = None
        left, right = self.match_brackets(bfr, self.search_window, sel)

        regions = [sublime.Region(sel.a, sel.b)]

        if left is not None and right is not None:
            bracket = self.brackets[left.type]
            left, right, regions, _ = self.run_plugin(bracket.name, left, right, regions)

        # Matched brackets
        if left is not None and right is not None and bracket is not None:
            self.save_regions(left, right, regions)

        # Unmatched brackets
        elif (left is not None or right is not None) and self.show_unmatched:
            self.save_incomplete_regions(left, right, regions)

        else:
            self.store_sel(regions)

    def escaped(self, pt, ignore_string_escape, scope):
        """
        Check if sub bracket in string scope is escaped.
        """

        if not ignore_string_escape:
            return False
        if scope and scope.startswith("string"):
            return self.string_escaped(pt)
        return False

    def string_escaped(self, pt):
        """
        Check if bracket is follows escaping characters.
        Account for if in string or regex string scope.
        """

        escaped = False
        start = pt - 1
        first = False
        if self.view.settings().get("bracket_string_escape_mode", self.default_string_escape_mode) == "string":
            first = True
        while self.view.substr(start) == "\\":
            if first:
                first = False
            else:
                escaped = False if escaped else True
            start -= 1
        return escaped

    def is_illegal_scope(self, pt, bracket_id, scope=None):
        """
        Check if scope at pt X should be ignored.
        """

        bracket = self.brackets[bracket_id]
        if self.sub_search_mode and not bracket.find_in_sub_search:
            return True
        illegal_scope = False
        # Scope sent in, so we must be scanning whatever this scope is
        if scope != None:
            if self.escaped(pt, bracket.ignore_string_escape, scope):
                illegal_scope = True
            return illegal_scope
        # for exception in bracket.scope_exclude_exceptions:
        elif len(bracket.scope_exclude_exceptions) and self.view.match_selector(pt, ", ".join(bracket.scope_exclude_exceptions)):
            pass
        elif len(bracket.scope_exclude) and self.view.match_selector(pt, ", ".join(bracket.scope_exclude)):
            illegal_scope = True
        return illegal_scope

    def compare(self, first, second, bfr, scope_bracket=False):
        """
        Compare brackets.  This function allows bracket plugins to add aditional logic.
        """

        if scope_bracket:
            match = first is not None and second is not None
        else:
            match = first.type == second.type
        if match:
            bracket = self.scopes[first.scope]["brackets"][first.type] if scope_bracket else self.brackets[first.type]
            try:
                if bracket.compare is not None and match:
                    match = bracket.compare(
                        bracket.name,
                        BracketRegion(first.begin, first.end),
                        BracketRegion(second.begin, second.end),
                        bfr
                    )
            except:
                bh_logging("Plugin Compare Error:\n%s" % str(traceback.format_exc()))
        return match

    def post_match(self, left, right, center, bfr, scope_bracket=False):
        """
        Peform special logic after a match has been made.
        This function allows bracket plugins to add aditional logic.
        """

        if left is not None:
            if scope_bracket:
                bracket = self.scopes[left.scope]["brackets"][left.type]
                bracket_scope = left.scope
            else:
                bracket = self.brackets[left.type]
            bracket_type = left.type
        elif right is not None:
            if scope_bracket:
                bracket = self.scopes[right.scope]["brackets"][right.type]
                bracket_scope = right.scope
            else:
                bracket = self.brackets[right.type]
            bracket_type = right.type
        else:
            return left, right

        self.bracket_style = bracket.style

        if bracket.post_match is not None:
            try:
                lbracket, rbracket, self.bracket_style = bracket.post_match(
                    self.view,
                    bracket.name,
                    bracket.style,
                    BracketRegion(left.begin, left.end) if left is not None else None,
                    BracketRegion(right.begin, right.end) if right is not None else None,
                    center,
                    bfr,
                    self.search_window
                )

                if scope_bracket:
                    left = ScopeEntry(lbracket.begin, lbracket.end, bracket_scope, bracket_type) if lbracket is not None else None
                    right = ScopeEntry(rbracket.begin, rbracket.end, bracket_scope, bracket_type) if rbracket is not None else None
                else:
                    left = BracketEntry(lbracket.begin, lbracket.end, bracket_type) if lbracket is not None else None
                    right = BracketEntry(rbracket.begin, rbracket.end, bracket_type) if rbracket is not None else None
            except:
                bh_logging("Plugin Post Match Error:\n%s" % str(traceback.format_exc()))
        return left, right

    def run_plugin(self, name, left, right, regions):
        """
        Run a bracket plugin.
        """

        lbracket = BracketRegion(left.begin, left.end)
        rbracket = BracketRegion(right.begin, right.end)
        nobracket = False

        if (
            ("__all__" in self.transform or name in self.transform) and
            self.plugin != None and
            self.plugin.is_enabled()
        ):
            lbracket, rbracket, regions, nobracket = self.plugin.run_command(self.view, name, lbracket, rbracket, regions)
            left = left.move(lbracket.begin, lbracket.end) if lbracket is not None else None
            right = right.move(rbracket.begin, rbracket.end) if rbracket is not None else None
        return left, right, regions, nobracket

    def match_scope_brackets(self, bfr, sel):
        """
        See if scope should be searched, and then check
        endcaps to determine if valid scope bracket.
        """

        center = sel.a
        left = None
        right = None
        scope_count = 0
        before_center = center - 1
        bracket_count = 0
        partial_find = None
        max_size = self.view.size() - 1
        selected_scope = None
        bracket = None

        # Cannot be inside a bracket pair if cursor is at zero
        if center == 0:
            return left, right, selected_scope, False

        # Identify if the cursor is in a scope with bracket definitions
        for s in self.scopes:
            scope = s["name"]
            extent = None
            exceed_limit = False
            if self.view.match_selector(center, scope) and self.view.match_selector(before_center, scope):
                extent = self.view.extract_scope(center)
                while not exceed_limit and extent.begin() != 0:
                    if self.view.match_selector(extent.begin() - 1, scope):
                        extent = extent.cover(self.view.extract_scope(extent.begin() - 1))
                        if extent.begin() < self.search_window[0] or extent.end() > self.search_window[1]:
                            extent = None
                            exceed_limit = True
                    else:
                        break
                while not exceed_limit and extent.end() != max_size:
                    if self.view.match_selector(extent.end(), scope):
                        extent = extent.cover(self.view.extract_scope(extent.end()))
                        if extent.begin() < self.search_window[0] or extent.end() > self.search_window[1]:
                            extent = None
                            exceed_limit = True
                    else:
                        break

            if extent is None:
                scope_count += 1
                continue

            # Search the bracket patterns of this scope
            # to determine if this scope matches the rules.
            bracket_count = 0
            scope_bfr = bfr[extent.begin():extent.end()]
            for b in s["brackets"]:
                m = b.open.search(scope_bfr)
                if m and m.group(1):
                    left = ScopeEntry(extent.begin() + m.start(1), extent.begin() + m.end(1), scope_count, bracket_count)
                m = b.close.search(scope_bfr)
                if m and m.group(1):
                    right = ScopeEntry(extent.begin() + m.start(1), extent.begin() + m.end(1), scope_count, bracket_count)
                if not self.compare(left, right, bfr, scope_bracket=True):
                    left, right = None, None
                # Track partial matches.  If a full match isn't found,
                # return the first partial match at the end.
                if partial_find is None and bool(left) != bool(right):
                    partial_find = (left, right)
                    left = None
                    right = None
                if left and right:
                    break
                bracket_count += 1
            if left and right:
                break
            scope_count += 1

        # Full match not found.  Return partial match (if any).
        if (left is None or right is None) and partial_find is not None:
            left, right = partial_find[0], partial_find[1]

        # Make sure cursor in highlighted sub group
        if (left and center <= left.begin) or (right and center >= right.end):
            left, right = None, None

        if left is not None:
            selected_scope = self.scopes[left.scope]["name"]
        elif right is not None:
            selected_scope = self.scopes[right.scope]["name"]

        if left is not None and right is not None:
            bracket = self.scopes[left.scope]["brackets"][left.type]
            if bracket.sub_search:
                self.sub_search_mode = True
                if self.sub_search(sel, (left.begin, right.end), bfr, scope):
                    return left, right, self.brackets[left.type], True
                elif bracket.sub_search_only:
                    left, right, bracket = None, None, None

        if self.adj_only:
            left, right = self.adjacent_check(left, right, center)

        left, right = self.post_match(left, right, center, bfr, scope_bracket=True)
        return left, right, bracket, False

    def match_brackets(self, bfr, window, sel, scope=None):
        """
        Regex bracket matching.
        """

        center = sel.a
        left = None
        right = None
        stack = []
        pattern = self.pattern if not self.sub_search_mode else self.sub_pattern
        bsearch = BracketSearch(bfr, window, center, pattern, self.is_illegal_scope, scope)
        for o in bsearch.get_open(BracketSearchSide.left):
            if len(stack) and bsearch.is_done(BracektSearchType.closing):
                if self.compare(o, stack[-1], bfr):
                    stack.pop()
                    continue
            for c in bsearch.get_close(BracketSearchSide.left):
                if o.end <= c.begin:
                    stack.append(c)
                    continue
                elif len(stack):
                    bsearch.remember(BracektSearchType.closing)
                    break

            if len(stack):
                b = stack.pop()
                if self.compare(o, b, bfr):
                    continue
            else:
                left = o
            break

        bsearch.reset_end_state()
        stack = []

        # Grab each closest closing right side bracket and attempt to match it.
        # If the closing bracket cannot be matched, select it.
        for c in bsearch.get_close(BracketSearchSide.right):
            if len(stack) and bsearch.is_done(BracektSearchType.opening):
                if self.compare(stack[-1], c, bfr):
                    stack.pop()
                    continue
            for o in bsearch.get_open(BracketSearchSide.right):
                if o.end <= c.begin:
                    stack.append(o)
                    continue
                else:
                    bsearch.remember(BracektSearchType.opening)
                    break

            if len(stack):
                b = stack.pop()
                if self.compare(b, c, bfr):
                    continue
            else:
                if left is None or self.compare(left, c, bfr):
                    right = c
            break

        if self.adj_only:
            left, right = self.adjacent_check(left, right, center)

        return self.post_match(left, right, center, bfr)

    def adjacent_check(self, left, right, center):
        if left and right:
            if left.end < center < right.begin:
                left, right = None, None
        elif (left and left.end < center) or (right and center < right.begin):
            left, right = None, None
        return left, right

bh_match = BhCore().match
bh_debug("Match object loaded.")


class BhListenerCommand(sublime_plugin.EventListener):
    """
    Manage when to kick off bracket matching.
    Try and reduce redundant requests by letting the
    background thread ensure certain needed match occurs
    """

    def on_load(self, view):
        """
        Search brackets on view load.
        """

        if self.ignore_event(view):
            return
        BhEventMgr.type = BH_MATCH_TYPE_SELECTION
        sublime.set_timeout(bh_run, 0)

    def on_modified(self, view):
        """
        Update highlighted brackets when the text changes.
        """

        if self.ignore_event(view):
            return
        BhEventMgr.type = BH_MATCH_TYPE_EDIT
        BhEventMgr.modified = True
        BhEventMgr.time = time()

    def on_activated(self, view):
        """
        Highlight brackets when the view gains focus again.
        """

        if self.ignore_event(view):
            return
        BhEventMgr.type = BH_MATCH_TYPE_SELECTION
        sublime.set_timeout(bh_run, 0)

    def on_selection_modified(self, view):
        """
        Highlight brackets when the selections change.
        """

        if self.ignore_event(view):
            return
        if BhEventMgr.type != BH_MATCH_TYPE_EDIT:
            BhEventMgr.type = BH_MATCH_TYPE_SELECTION
        now = time()
        if now - BhEventMgr.time > BhEventMgr.wait_time:
            sublime.set_timeout(bh_run, 0)
        else:
            BhEventMgr.modified = True
            BhEventMgr.time = now

    def ignore_event(self, view):
        """
        Ignore request to highlight if the view is a widget,
        or if it is too soon to accept an event.
        """

        return (view.settings().get('is_widget') or BhEventMgr.ignore_all)


def bh_run():
    """
    Kick off matching of brackets
    """

    BhEventMgr.modified = False
    window = sublime.active_window()
    view = window.active_view() if window != None else None
    BhEventMgr.ignore_all = True
    bh_match(view, True if BhEventMgr.type == BH_MATCH_TYPE_EDIT else False)
    BhEventMgr.ignore_all = False
    BhEventMgr.time = time()


def bh_loop():
    """
    Start thread that will ensure highlighting happens after a barage of events
    Initial highlight is instant, but subsequent events in close succession will
    be ignored and then accounted for with one match by this thread
    """

    while not BhThreadMgr.restart:
        if BhEventMgr.modified == True and time() - BhEventMgr.time > BhEventMgr.wait_time:
            sublime.set_timeout(bh_run, 0)
        sleep(0.5)

    if BhThreadMgr.restart:
        BhThreadMgr.restart = False
        sublime.set_timeout(lambda: thread.start_new_thread(bh_loop, ()), 0)

if sublime.load_settings("bh_core.sublime-settings").get('high_visibility_enabled_by_default', False):
    HIGH_VISIBILITY = True

if not 'running_bh_loop' in globals():
    running_bh_loop = True
    thread.start_new_thread(bh_loop, ())
    bh_debug("Starting Thread")
else:
    bh_debug("Restarting Thread")
    BhThreadMgr.restart = True
