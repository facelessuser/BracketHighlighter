from os.path import basename, exists, join, normpath
import sublime
import sublime_plugin
from time import time, sleep
import thread
import re
import sys
import imp
from bh_plugin import BracketPlugin, BracketRegion, BH_MODULES
from collections import namedtuple
import traceback

BH_MATCH_TYPE_NONE = 0
BH_MATCH_TYPE_SELECTION = 1
BH_MATCH_TYPE_EDIT = 2


def underline(regions):
    r = []
    for region in regions:
        start = region.begin()
        end = region.end()
        while start < end:
            r.append(sublime.Region(start))
            start += 1
    return r


def load_modules(obj, loaded):
    plib = obj.get("plugin_library")
    if plib is None:
        return

    if plib.startswith("bh_modules"):
        if "bh_modules" not in loaded:
            imp.load_source("bh_modules", join(BH_MODULES, "bh_modules", "__init__.py"))
            loaded.add("bh_modules")
        path_name = join(BH_MODULES, normpath(plib.replace('.', '/')))
    else:
        path_name = join(sublime.packages_path(), normpath(plib.replace('.', '/')))

    if not exists(path_name):
        path_name += ".py"
        if not exists(path_name):
            print "BracketHighlighter: Could not load module %s" % plib
            return
    try:
        if plib in loaded:
            module = sys.modules[plib]
        else:
            module = imp.load_source(plib, path_name)
        obj["compare"] = getattr(module, "compare", None)
        obj["post_match"] = getattr(module, "post_match", None)
        loaded.add(plib)
    except:
        print "BracketHighlighter: Could not load module %s" % plib
        raise


def select_bracket_style(option):
    style = sublime.HIDE_ON_MINIMAP
    if option == "outline":
        style |= sublime.DRAW_OUTLINED
    elif option == "none":
        style |= sublime.HIDDEN
    elif option == "underline":
        style |= sublime.DRAW_EMPTY_AS_OVERWRITE
    return style


def select_bracket_icons(option, settings):
    icon = ""
    small_icon = ""
    icon_path = settings.get("icon_path", "Theme - Default").replace('\\', '/').strip('/')
    # Icon exist?
    if (
        exists(normpath(join(sublime.packages_path(), icon_path, option + ".png"))) and
        not option == "none" and not option == ""
    ):
        icon = "../%s/%s" % (icon_path, option)
        if exists(normpath(join(sublime.packages_path(), icon_path, option + "_small.png"))):
            small_icon = "../%s/%s" % (icon_path, option + "_small")
    return icon, small_icon


def exclude_bracket(enabled, filter_type, language_list, language):
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


class Pref(object):
    @classmethod
    def load(cls):
        cls.wait_time = 0.12
        cls.time = time()
        cls.modified = False
        cls.type = BH_MATCH_TYPE_SELECTION
        cls.ignore_all = False

Pref.load()


class BracketEntry(namedtuple('BracketEntry', ['begin', 'end', 'type'], verbose=False)):
    def move(self, begin, end):
        return self._replace(begin=begin, end=end)

    def size(self):
        return abs(self.begin - self.end)

    def toregion(self):
        return sublime.Region(self.begin, self.end)


class ScopeEntry(namedtuple('ScopeEntry', ['begin', 'end', 'scope', 'type'], verbose=False)):
    def move(self, begin, end):
        return self._replace(begin=begin, end=end)

    def size(self):
        return abs(self.begin - self.end)

    def toregion(self):
        return sublime.Region(self.begin, self.end)


class BracketSearch(object):
    def __init__(self, bfr, window, center, pattern, scope_check, scope, match_type):
        self.center = center
        self.pattern = pattern
        self.match_type = match_type
        self.bfr = bfr
        self.scope = scope
        self.scope_check = scope_check
        self.prev_match = None
        self.return_prev = False
        self.done = False
        self.start = None
        self.left = []
        self.right = []
        self.findall(window)

    def reset_end_state(self):
        self.start = None
        self.done = False
        self.prev_match = None
        self.return_prev = False

    def remember(self):
        self.return_prev = True
        self.done = False

    def findall(self, window):
        for m in self.pattern.finditer(self.bfr, window[0], window[1]):
            g = m.lastindex
            try:
                start = m.start(g + 1)
                end = m.end(g + 1)
            except:
                continue
            bracket_id = (g - 1) / 2
            if not self.scope_check(start, bracket_id, self.scope):
                if (end <= self.center if self.match_type else start < self.center):
                    self.left.append(BracketEntry(start, end, bracket_id))
                elif (end > self.center if self.match_type else start >= self.center):
                    self.right.append(BracketEntry(start, end, bracket_id))

    def get_brackets(self, bracket_code):
        if self.done:
            return
        if self.return_prev:
            self.return_prev = False
            yield self.prev_match
        if bracket_code == 0:
            if self.start is None:
                self.start = len(self.left)
            for x in reversed(range(0, self.start)):
                b = self.left[x]
                self.prev_match = b
                self.start -= 1
                yield b
        else:
            if self.start is None:
                self.start = 0
            for x in range(self.start, len(self.right)):
                b = self.right[x]
                self.prev_match = b
                self.start += 1
                yield b

        self.done = True


class BracketDefinition(object):
    def __init__(self, bracket, settings):
        self.name = bracket["name"]
        self.color = bracket["color"]
        self.selections = []
        self.compare = bracket.get("compare")
        self.find_in_sub_search = bracket.get("find_in_sub_search", False)
        self.post_match = bracket.get("post_match")
        self.scope_exclude_exceptions = bracket.get("scope_exclude_exceptions", [])
        self.scope_exclude = bracket.get("scope_exclude", [])
        self.style = select_bracket_style(bracket["style"])
        self.underline = self.style & sublime.DRAW_EMPTY_AS_OVERWRITE
        self.icon, self.small_icon = select_bracket_icons(bracket["icon"], settings)
        self.ignore_string_escape = bracket.get("ignore_string_escape", False)
        self.no_icon = ""


class ScopeDefinition(object):
    def __init__(self, bracket, settings):
        self.open = re.compile("\\A" + bracket.get("open", "."), re.MULTILINE | re.IGNORECASE)
        self.close = re.compile(bracket.get("close", ".") + "\\Z", re.MULTILINE | re.IGNORECASE)
        self.selections = []
        self.name = bracket["name"]
        self.color = bracket["color"]
        sub_search = bracket.get("sub_bracket_search", "false")
        self.sub_search_only = sub_search == "only"
        self.sub_search = self.sub_search_only == True or sub_search == "true"
        self.compare = bracket.get("compare")
        self.post_match = bracket.get("post_match")
        self.scopes = bracket["scopes"]
        self.style = select_bracket_style(bracket["style"])
        self.underline = self.style & sublime.DRAW_EMPTY_AS_OVERWRITE
        self.icon, self.small_icon = select_bracket_icons(bracket["icon"], settings)
        self.no_icon = ""


class BhToggleStringEscapeModeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        default_mode = sublime.load_settings("bh_core.sublime-settings").get('bracket_string_escape_mode', 'string')
        if self.view.settings().get('bracket_string_escape_mode', default_mode) == "regex":
            self.view.settings().set('bracket_string_escape_mode', "string")
            sublime.status_message("Bracket String Escape Mode: string")
        else:
            self.view.settings().set('bracket_string_escape_mode', "regex")
            sublime.status_message("Bracket String Escape Mode: regex")


class BhShowStringEscapeModeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        default_mode = sublime.load_settings("BracketHighlighter.sublime-settings").get('bracket_string_escape_mode', 'string')
        sublime.status_message("Bracket String Escape Mode: %s" % self.view.settings().get('bracket_string_escape_mode', default_mode))


class BhKeyCommand(sublime_plugin.WindowCommand):
    def run(self, threshold=True, lines=False, adjacent=False, ignore={}, plugin={}):
        # Override events
        Pref.ignore_all = True
        Pref.modified = False
        BhCore(
            threshold,
            lines,
            adjacent,
            ignore,
            plugin
        ).match(self.window.active_view())
        # Reset event settings
        Pref.ignore_all = False
        Pref.time = time()


class BhCore(object):
    def __init__(self, override_thresh=False, count_lines=False, adj_only=None, ignore={}, plugin={}):
        self.settings = sublime.load_settings("bh_core.sublime-settings")
        self.settings.add_on_change('reload', lambda: self.setup())
        self.setup(override_thresh, count_lines, adj_only, ignore, plugin)

    def setup(self, override_thresh=False, count_lines=False, adj_only=None, ignore={}, plugin={}):
        # Init view params
        self.last_id_view = None
        self.last_id_sel = None
        self.view_tracker = (None, None)
        self.ignore_threshold = override_thresh
        self.adj_only = adj_only if adj_only is not None else bool(self.settings.get("match_only_adjacent", False))
        self.auto_selection_threshold = int(self.settings.get("auto_selection_threshold", 10))
        self.no_multi_select_icons = bool(self.settings.get("no_multi_select_icons", False))
        self.count_lines = count_lines
        self.default_string_escape_mode = self.settings.get('bracket_string_escape_mode', "string")

        # Init bracket objects
        self.bracket_types = self.settings.get("brackets", [])
        incomplete = self.settings.get(
            "incomplete",
            {
                "icon": "dot",
                "color": "keyword",
                "style": "outline",
                "scope_exclude": [],
                "enabled": True
            }
        )
        incomplete["name"] = "incomplete"
        self.incomplete = BracketDefinition(incomplete, self.settings)

        self.scope_types = self.settings.get("scope_brackets", [])

        # Init selection params
        self.use_selection_threshold = True
        self.selection_threshold = self.settings.get("search_threshold", 5000)
        self.new_select = False
        self.loaded_modules = set([])

        # Init plugin
        self.plugin = None
        self.transform = set([])
        if 'command' in plugin:
            self.plugin = BracketPlugin(plugin, self.loaded_modules)
            self.new_select = True
            if 'type' in plugin:
                for t in plugin["type"]:
                    self.transform.add(t)

    def init_brackets(self, language):
        self.find_regex_open = "(?:"
        self.find_regex_close = "(?:"
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
        current_brackets = []

        # Initialize brackets
        self.incomplete.selections = []

        for params in self.bracket_types:
            if (
                not exclude_bracket(
                    params.get("enabled", True),
                    params.get("language_filter", "blacklist"),
                    params.get("language_list", []),
                    language
                )
            ):
                # reload_modules(params, reloaded)
                if params["open"] is not None and params["close"] is not None:
                    try:
                        load_modules(params, loaded_modules)
                        entry = BracketDefinition(params, self.settings)
                        self.brackets.append(entry)
                        self.find_regex_close += "(" + params["close"] + ")|"
                        self.find_regex_open += "(" + params["open"] + ")|"
                        current_brackets.append(entry.name)
                    except Exception, e:
                        print e

        scope_count = 0
        for params in self.scope_types:
            if (
                not exclude_bracket(
                    params.get("enabled", True),
                    params.get("language_filter", "blacklist"),
                    params.get("language_list", []),
                    language
                )
            ):
                # reload_modules(params, reloaded)
                if params["open"] is not None and params["close"] is not None:
                    try:
                        load_modules(params, loaded_modules)
                        entry = ScopeDefinition(params, self.settings)
                        for x in entry.scopes:
                            if x not in scopes:
                                scopes[x] = scope_count
                                scope_count += 1
                                self.scopes.append({"name": x, "brackets": [entry]})
                            else:
                                self.scopes[scopes[x]]["brackets"].append(entry)
                            current_brackets.append(entry.name)
                    except Exception, e:
                        print e

        if len(self.brackets):
            self.find_regex_open = self.find_regex_open[0:len(self.find_regex_open) - 1] + ")"
            self.find_regex_close = self.find_regex_close[0:len(self.find_regex_close) - 1] + ")"
            self.pattern_open = re.compile(self.find_regex_open, re.MULTILINE | re.IGNORECASE)
            self.pattern_close = re.compile(self.find_regex_close, re.MULTILINE | re.IGNORECASE)
            self.enabled = True
        self.view.settings().set("bh_registered_brackets", current_brackets)

    def init_match(self):
        self.chars = 0
        self.lines = 0
        syntax = self.view.settings().get('syntax')
        language = basename(syntax).replace('.tmLanguage', '').lower() if syntax != None else "plain text"

        if language != self.view_tracker[0] or self.view.id() != self.view_tracker[1]:
            self.init_brackets(language)
        else:
            for b in (self.brackets + [self.incomplete]):
                b.selections = []
            for s in self.scopes:
                for b in s["brackets"]:
                    b.selections = []

    def get_bracket_type(self, name, begin, end):
        entry = None
        count = 0
        for b in (self.brackets + [self.incomplete]):
            if b.name == name:
                entry = BracketEntry(begin, end, count)
            count += 1
        count = 0
        for s in self.scopes:
            sub_count = 0
            for b in s["brackets"]:
                if b.name == name:
                    entry = ScopeEntry(begin, end, count, sub_count)
                sub_count += 1
        return entry

    def unique(self):
        id_view = self.view.id()
        id_sel = "".join([str(sel.a) for sel in self.view.sel()])
        is_unique = False
        if id_view != self.last_id_view or id_sel != self.last_id_sel:
            self.last_id_view = id_view
            self.last_id_sel = id_sel
            is_unique = True
        return is_unique

    def store_sel(self, regions):
        if self.new_select:
            for region in regions:
                self.sels.append(region)

    def change_sel(self):
        if self.new_select and len(self.sels) > 0:
            if self.multi_select == False:
                self.view.show(self.sels[0])
            self.view.sel().clear()
            map(lambda x: self.view.sel().add(x), self.sels)

    def highlight(self, view):
        for region_key in self.view.settings().get("bh_regions", []):
            self.view.erase_regions(region_key)

        regions = []
        icon_type = "no_icon"
        if not self.no_multi_select_icons or not self.multi_select:
            icon_type = "small_icon" if self.view.line_height() < 16 else "icon"
        for b in (self.brackets + [self.incomplete]):
            if len(b.selections):
                self.view.add_regions(
                    "bh_" + b.name,
                    b.selections,
                    b.color,
                    getattr(b, icon_type),
                    b.style
                )
                regions.append("bh_" + b.name)
        for s in self.scopes:
            for b in s["brackets"]:
                if len(b.selections):
                    self.view.add_regions(
                        "bh_" + b.name,
                        b.selections,
                        b.color,
                        getattr(b, icon_type),
                        b.style
                    )
                    regions.append("bh_" + b.name)
        self.view.settings().set("bh_regions", regions)

    def get_search_bfr(self, sel):
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
        if view == None:
            return
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
                return

            # Abort if selections are beyond the threshold
            if self.use_selection_threshold and num_sels >= self.selection_threshold:
                self.highlight(view)
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

    def find_scopes(self, bfr, sel):
        # Search buffer
        left, right, bracket, sub_matched = self.match_scope_brackets(bfr, sel)
        if sub_matched:
            return True
        regions = [sublime.Region(sel.a, sel.b)]

        if left is not None and right is not None:
            left, right, regions = self.run_plugin(bracket.name, left, right, regions)

        if left is not None and right is not None:
            if self.count_lines:
                self.chars += abs(right.begin - left.end)
                self.lines += abs(self.view.rowcol(right.begin)[0] - self.view.rowcol(left.end)[0] + 1)
            if bracket.underline:
                bracket.selections += underline((left.toregion(), right.toregion()))
            else:
                bracket.selections += [left.toregion(), right.toregion()]
            self.store_sel(regions)
            return True
        elif left is not None or right is not None:
            found = left if left is not None else right
            bracket = self.incomplete
            if bracket.underline:
                bracket.selections += underline((found.toregion(),))
            else:
                bracket.selections += [found.toregion()]
            return True
        return False

    def sub_search(self, sel, search_window, bfr, scope=None):
        bracket = None
        left, right = self.match_brackets(bfr, search_window, sel, scope)

        regions = [sublime.Region(sel.a, sel.b)]

        if left is not None and right is not None:
            bracket = self.brackets[left.type]
            left, right, regions = self.run_plugin(bracket.name, left, right, regions)

        # Matched brackets
        if left is not None and right is not None and bracket is not None:
            if self.count_lines:
                self.chars += abs(right.begin - left.end)
                self.lines += abs(self.view.rowcol(right.begin)[0] - self.view.rowcol(left.end)[0] + 1)
            if bracket.underline:
                bracket.selections += underline((left.toregion(), right.toregion()))
            else:
                bracket.selections += [left.toregion(), right.toregion()]
            self.store_sel(regions)
            return True
        return False

    def find_matches(self, bfr, sel):
        bracket = None
        left, right = self.match_brackets(bfr, self.search_window, sel)

        regions = [sublime.Region(sel.a, sel.b)]

        if left is not None and right is not None:
            bracket = self.brackets[left.type]
            left, right, regions = self.run_plugin(bracket.name, left, right, regions)

        # Matched brackets
        if left is not None and right is not None and bracket is not None:
            if self.count_lines:
                self.chars += abs(right.begin - left.end)
                self.lines += abs(self.view.rowcol(right.begin)[0] - self.view.rowcol(left.end)[0] + 1)
            if bracket.underline:
                bracket.selections += underline((left.toregion(), right.toregion()))
            else:
                bracket.selections += [left.toregion(), right.toregion()]
            self.store_sel(regions)

        # Unmatched brackets
        elif left is not None or right is not None:
            found = left if left is not None else right
            bracket = self.incomplete
            if bracket.underline:
                bracket.selections += underline((found.toregion(),))
            else:
                bracket.selections += [found.toregion()]

    def escaped(self, pt, ignore_string_escape, scope):
        if not ignore_string_escape:
            return False
        if scope and scope.startswith("string"):
            return self.string_escaped(pt)
        return False

    def string_escaped(self, pt):
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

    def compare(self, first, second, bfr):
        bracket = self.brackets[first.type]
        match = first.type == second.type
        if bracket.compare is not None and match:
            match = bracket.compare(
                bracket.name,
                BracketRegion(first.begin, first.end),
                BracketRegion(second.begin, second.end),
                bfr
            )
        return match

    def scope_compare(self, left, right, bfr):
        left, right = None, None
        match = right and left
        if match:
            bracket = self.scopes[left.scope]["brackets"][left.type]
            match = True
            try:
                if bracket.compare is not None:
                    match = bracket.compare(
                        BracketRegion(left.begin, left.end, bracket.name),
                        BracketRegion(right.begin, right.end, bracket.name),
                        bfr
                    )
            except:
                print "BracketHighlighter: Plugin Compare Error:\n%s" % str(traceback.format_exc())
        return match

    def scope_post_match(self, left, right, center, bfr):
        if left is not None:
            bracket = self.scopes[left.scope]["brackets"][left.type]
            bracket_scope = left.scope
            bracket_type = left.type
        elif right is not None:
            bracket = self.scopes[right.scope]["brackets"][right.type]
            bracket_scope = right.scope
            bracket_type = right.type
        else:
            return left, right

        if bracket.post_match is not None:
            try:
                lbracket, rbracket, bracket_name = bracket.post_match(
                    self.view,
                    bracket.name,
                    BracketRegion(left.begin, left.end) if left is not None else None,
                    BracketRegion(right.begin, right.end) if right is not None else None,
                    center,
                    bfr,
                    self.search_window
                )
                if bracket_name != bracket.name:
                    left = self.get_bracket_type(bracket_name, lbracket.begin, lbracket.end) if lbracket is not None else None
                    right = self.get_bracket_type(bracket_name, rbracket.begin, rbracket.end) if rbracket is not None else None
                    if left is not None or right is not None:
                        return left, right

                left = ScopeEntry(lbracket.begin, lbracket.end, bracket_scope, bracket_type) if lbracket is not None else None
                right = ScopeEntry(rbracket.begin, rbracket.end, bracket_scope, bracket_type) if rbracket is not None else None
            except:
                print "BracketHighlighter: Plugin Post Match Error:\n%s" % str(traceback.format_exc())
        return left, right

    def post_match(self, left, right, center, bfr):
        if left is not None:
            bracket = self.brackets[left.type]
            bracket_type = left.type
        elif right is not None:
            bracket = self.brackets[right.type]
            bracket_type = right.type
        else:
            return left, right

        if bracket.post_match is not None:
            try:
                lbracket, rbracket, bracket_name = bracket.post_match(
                    self.view,
                    bracket.name,
                    BracketRegion(left.begin, left.end) if left is not None else None,
                    BracketRegion(right.begin, right.end) if right is not None else None,
                    center,
                    bfr,
                    self.search_window
                )
                if bracket_name != bracket.name:
                    left = self.get_bracket_type(bracket_name, lbracket.begin, lbracket.end) if lbracket is not None else None
                    right = self.get_bracket_type(bracket_name, rbracket.begin, rbracket.end) if rbracket is not None else None
                    if left is not None or right is not None:
                        return left, right
                left = BracketEntry(lbracket.begin, lbracket.end, bracket_type) if lbracket is not None else None
                right = BracketEntry(rbracket.begin, rbracket.end, bracket_type) if rbracket is not None else None
            except:
                print "BracketHighlighter: Plugin Compare Error:\n%s" % str(traceback.format_exc())

        return left, right

    def run_plugin(self, name, left, right, regions):
        lbracket = BracketRegion(left.begin, left.end)
        rbracket = BracketRegion(right.begin, right.end)

        if (
            ("__all__" in self.transform or name in self.transform) and
            self.plugin != None and
            self.plugin.is_enabled()
        ):
            lbracket, rbracket, regions = self.plugin.run_command(self.view, name, lbracket, rbracket, regions)
            left = left.move(lbracket.begin, lbracket.end) if lbracket is not None else None
            right = right.move(rbracket.begin, rbracket.end) if rbracket is not None else None
        return left, right, regions

    def match_scope_brackets(self, bfr, sel):
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
                self.scope_compare(left, right, bfr)
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

        left, right = self.scope_post_match(left, right, center, bfr)
        return left, right, bracket, False

    def match_brackets(self, bfr, window, sel, scope=None):
        center = sel.a
        left = None
        right = None
        stack = []
        osearch = BracketSearch(bfr, window, center, self.pattern_open, self.is_illegal_scope, scope, 0)
        csearch = BracketSearch(bfr, window, center, self.pattern_close, self.is_illegal_scope, scope, 1)
        for o in osearch.get_brackets(0):
            if len(stack) and csearch.done:
                if self.compare(o, stack[-1], bfr):
                    stack.pop()
                    continue
            for c in csearch.get_brackets(0):
                if o.end <= c.begin:
                    stack.append(c)
                    continue
                elif len(stack):
                    csearch.remember()
                    break

            if len(stack):
                b = stack.pop()
                if self.compare(o, b, bfr):
                    continue
            else:
                left = o
            break

        osearch.reset_end_state()
        csearch.reset_end_state()
        stack = []

        # Grab each closest closing right side bracket and attempt to match it.
        # If the closing bracket cannot be matched, select it.
        for c in csearch.get_brackets(1):
            if len(stack) and osearch.done:
                if self.compare(stack[-1], c, bfr):
                    stack.pop()
                    continue
            for o in osearch.get_brackets(1):
                if o.end <= c.begin:
                    stack.append(o)
                    continue
                else:
                    osearch.remember()
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


class BhListenerCommand(sublime_plugin.EventListener):
    """
    Manage when to kick off bracket matching.
    Try and reduce redundant requests by letting the
    background thread ensure certain needed match occurs
    """

    def on_load(self, view):
        if self.ignore_event(view):
            return
        Pref.type = BH_MATCH_TYPE_SELECTION
        sublime.set_timeout(lambda: bh_run(), 0)

    def on_modified(self, view):
        if self.ignore_event(view):
            return
        Pref.type = BH_MATCH_TYPE_EDIT
        Pref.modified = True
        Pref.time = time()

    def on_activated(self, view):
        if self.ignore_event(view):
            return
        Pref.type = BH_MATCH_TYPE_SELECTION
        sublime.set_timeout(lambda: bh_run(), 0)

    def on_selection_modified(self, view):
        if self.ignore_event(view):
            return
        if Pref.type != BH_MATCH_TYPE_EDIT:
            Pref.type = BH_MATCH_TYPE_SELECTION
        now = time()
        if now - Pref.time > Pref.wait_time:
            sublime.set_timeout(lambda: bh_run(), 0)
        else:
            Pref.modified = True
            Pref.time = now

    def ignore_event(self, view):
        return (view.settings().get('is_widget') or Pref.ignore_all)


def bh_run():
    """
    Kick off matching of brackets
    """

    Pref.modified = False
    window = sublime.active_window()
    view = window.active_view() if window != None else None
    Pref.ignore_all = True
    bh_match(view, True if Pref.type == BH_MATCH_TYPE_EDIT else False)
    Pref.ignore_all = False
    Pref.time = time()


def bh_loop():
    """
    Start thread that will ensure highlighting happens after a barage of events
    Initial highlight is instant, but subsequent events in close succession will
    be ignored and then accounted for with one match by this thread
    """

    while True:
        if Pref.modified == True and time() - Pref.time > Pref.wait_time:
            sublime.set_timeout(lambda: bh_run(), 0)
        sleep(0.5)

if not 'running_bh_loop' in globals():
    running_bh_loop = True
    thread.start_new_thread(bh_loop, ())
