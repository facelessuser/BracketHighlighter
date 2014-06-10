import sublime
import sublime_plugin
from os.path import basename, join
from time import time, sleep
import thread
import traceback
import ure
import bh_plugin
import bh_search
import bh_regions
import bh_rules
from bh_logging import debug, log

bh_match = None

BH_MATCH_TYPE_NONE = 0
BH_MATCH_TYPE_SELECTION = 1
BH_MATCH_TYPE_EDIT = 2
GLOBAL_ENABLE = True
HIGH_VISIBILITY = False


####################
# Match Code
####################
class BhCore(object):
    """
    Bracket matching class.
    """
    plugin_reload = False

    ####################
    # Match Setup
    ####################
    def __init__(
        self, override_thresh=False, count_lines=False,
        adj_only=None, no_outside_adj=False,
        ignore={}, plugin={}, keycommand=False
    ):
        """
        Load settings and setup reload events if settings changes.
        """

        self.settings = sublime.load_settings("bh_core.sublime-settings")
        self.keycommand = keycommand
        if not keycommand:
            self.settings.clear_on_change('reload')
            self.settings.add_on_change('reload', self.setup)
        self.setup(override_thresh, count_lines, adj_only, no_outside_adj, ignore, plugin)

    def setup(self, override_thresh=False, count_lines=False, adj_only=None, no_outside_adj=False, ignore={}, plugin={}):
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
        self.kill_highlight_on_threshold = bool(self.settings.get("kill_highlight_on_threshold", False))

        # Init search object
        self.rules = bh_rules.SearchRules(
            self.settings.get("brackets", []) + self.settings.get("user_brackets", []),
            self.settings.get("scope_brackets", []) + self.settings.get("user_scope_brackets", []),
            str(self.settings.get('bracket_string_escape_mode', "string")),
            False if no_outside_adj else self.settings.get("bracket_outside_adjacent", False)
        )

        # Init selection params
        self.use_selection_threshold = True
        self.selection_threshold = int(self.settings.get("search_threshold", 5000))
        self.loaded_modules = set([])

        # Init plugin
        alter_select = False
        self.plugin = None
        self.plugin_targets = set([])
        if 'command' in plugin:
            self.plugin = bh_plugin.BracketPlugin(plugin, self.loaded_modules)
            alter_select = True
            if 'type' in plugin:
                for target in plugin["type"]:
                    self.plugin_targets.add(target)

        # Region selection, highlight, managment
        self.regions = bh_regions.BhRegion(alter_select, count_lines)

    def refresh_rules(self, language):
        """
        Reload rules
        """

        loaded_modules = self.loaded_modules.copy()

        self.rules.load_rules(
            language,
            loaded_modules
        )

    def init_match(self, num_sels):
        """
        Reset matching settings for the current view's syntax.
        """

        syntax = self.view.settings().get('syntax')
        language = basename(syntax).replace('.tmLanguage', '').lower() if syntax is not None else "plain text"

        self.regions.reset(self.view, num_sels)

        if language != self.view_tracker[0] or self.view.id() != self.view_tracker[1]:
            self.view_tracker = (language, self.view.id())
            self.refresh_rules(language)
            self.regions.set_show_unmatched(language)

    def unique(self, sels):
        """
        Check if the current selection(s) is different from the last.
        """

        id_view = self.view.id()
        id_sel = "".join([str(sel.a) for sel in sels])
        is_unique = False
        if id_view != self.last_id_view or id_sel != self.last_id_sel:
            self.last_id_view = id_view
            self.last_id_sel = id_sel
            is_unique = True
        return is_unique

    ####################
    # Plugin
    ####################
    def run_plugin(self, name, left, right, regions):
        """
        Run a bracket plugin.
        """

        lbracket = bh_plugin.BracketRegion(left.begin, left.end)
        rbracket = bh_plugin.BracketRegion(right.begin, right.end)
        nobracket = False

        if (
            ("__all__" in self.plugin_targets or name in self.plugin_targets) and
            self.plugin is not None and
            self.plugin.is_enabled()
        ):
            lbracket, rbracket, regions, nobracket = self.plugin.run_command(self.view, name, lbracket, rbracket, regions)
            left = left.move(lbracket.begin, lbracket.end) if lbracket is not None else None
            right = right.move(rbracket.begin, rbracket.end) if rbracket is not None else None
        return left, right, regions, nobracket

    def validate(self, b, bracket_type, scope_bracket=False):
        """
        Validate bracket.
        """

        match = True

        if not self.rules.check_validate:
            return match

        bracket = self.rules.scopes[b.scope]["brackets"][b.type] if scope_bracket else self.rules.brackets[b.type]
        if bracket.validate is not None:
            try:
                match = bracket.validate(
                    bracket.name,
                    bh_plugin.BracketRegion(b.begin, b.end),
                    bracket_type,
                    self.search.get_buffer()
                )
            except:
                log("Plugin Bracket Find Error:\n%s" % str(traceback.format_exc()))
        return match

    def compare(self, first, second, scope_bracket=False):
        """
        Compare brackets.  This function allows bracket plugins to add aditional logic.
        """

        if scope_bracket:
            match = first is not None and second is not None
        else:
            match = first.type == second.type

        if not self.rules.check_compare:
            return match

        if match:
            bracket = self.rules.scopes[first.scope]["brackets"][first.type] if scope_bracket else self.rules.brackets[first.type]
            try:
                if bracket.compare is not None and match:
                    match = bracket.compare(
                        bracket.name,
                        bh_plugin.BracketRegion(first.begin, first.end),
                        bh_plugin.BracketRegion(second.begin, second.end),
                        self.search.get_buffer()
                    )
            except:
                log("Plugin Compare Error:\n%s" % str(traceback.format_exc()))
        return match

    def post_match(self, left, right, center, scope_bracket=False):
        """
        Peform special logic after a match has been made.
        This function allows bracket plugins to add aditional logic.
        """

        if left is not None:
            if scope_bracket:
                bracket = self.rules.scopes[left.scope]["brackets"][left.type]
                bracket_scope = left.scope
            else:
                bracket = self.rules.brackets[left.type]
            bracket_type = left.type
        elif right is not None:
            if scope_bracket:
                bracket = self.rules.scopes[right.scope]["brackets"][right.type]
                bracket_scope = right.scope
            else:
                bracket = self.rules.brackets[right.type]
            bracket_type = right.type
        else:
            return left, right

        self.bracket_style = bracket.style

        if not self.rules.check_post_match:
            return left, right

        if bracket.post_match is not None:
            try:
                lbracket, rbracket, self.bracket_style = bracket.post_match(
                    self.view,
                    bracket.name,
                    bracket.style,
                    bh_plugin.BracketRegion(left.begin, left.end) if left is not None else None,
                    bh_plugin.BracketRegion(right.begin, right.end) if right is not None else None,
                    center,
                    self.search.get_buffer(),
                    self.search.search_window
                )

                if scope_bracket:
                    left = bh_search.ScopeEntry(lbracket.begin, lbracket.end, bracket_scope, bracket_type) if lbracket is not None else None
                    right = bh_search.ScopeEntry(rbracket.begin, rbracket.end, bracket_scope, bracket_type) if rbracket is not None else None
                else:
                    left = bh_search.BracketEntry(lbracket.begin, lbracket.end, bracket_type) if lbracket is not None else None
                    right = bh_search.BracketEntry(rbracket.begin, rbracket.end, bracket_type) if rbracket is not None else None
            except:
                log("Plugin Post Match Error:\n%s" % str(traceback.format_exc()))

        return left, right

    ####################
    # Matching
    ####################
    def match(self, view, force_match=True):
        """
        Preform matching brackets surround the selection(s)
        """

        if view is None:
            return

        # Ensure nothing else calls BH until done
        view.settings().set("BracketHighlighterBusy", True)

        # Abort if disabled
        if not GLOBAL_ENABLE:
            for region_key in view.settings().get("bh_regions", []):
                view.erase_regions(region_key)
            view.settings().set("BracketHighlighterBusy", False)
            return

        # Handle key command quirks
        if self.keycommand:
            BhCore.plugin_reload = True

        if not self.keycommand and BhCore.plugin_reload:
            self.setup()
            BhCore.plugin_reload = False

        # Setup view
        self.view = view
        sels = view.sel()
        num_sels = len(sels)

        # Abort if selections are beyond the threshold and "kill" is enabled
        if not self.ignore_threshold and self.kill_highlight_on_threshold:
            if self.use_selection_threshold and num_sels > self.auto_selection_threshold:
                self.regions.reset(view, num_sels)
                self.regions.highlight(HIGH_VISIBILITY)
                view.settings().set("BracketHighlighterBusy", False)
                return

        # Initialize
        if self.unique(sels) or force_match:
            # Prepare for match
            self.init_match(num_sels)

            # Nothing to search for
            if not self.rules.enabled:
                view.settings().set("BracketHighlighterBusy", False)
                return

            # Process selections.
            multi_select_count = 0
            for sel in sels:
                if not self.ignore_threshold and multi_select_count >= self.auto_selection_threshold:
                    # Exceeded threshold, only what must be done
                    # and break
                    if not self.regions.alter_select:
                        break
                    self.regions.store_sel([sel])
                    continue

                # Subsearch guard for recursive matching of scopes
                self.recursive_guard = False

                # Prepare for search
                self.bracket_style = None
                self.search = bh_search.Search(
                    view, self.rules,
                    sel, self.selection_threshold if not self.ignore_threshold else None
                )

                # Find and match
                if not self.find_scopes(sel):
                    self.sub_search_mode = False
                    self.find_matches(sel)
                multi_select_count += 1

        # Highlight, focus, and display lines etc.
        self.regions.highlight(HIGH_VISIBILITY)

        # Free up BH
        self.search = None
        self.view = None
        view.settings().set("BracketHighlighterBusy", False)

    def sub_search(self, sel, scope=None):
        """
        Search a scope bracket match for bracekts within.
        """

        # Protect against recursive search of scopes
        self.recursive_guard = True

        # Find brackets inside scope
        bracket = None
        left, right, scope_adj = self.match_brackets(sel, scope)

        regions = [sublime.Region(sel.a, sel.b)]

        if left is not None and right is not None:
            bracket = self.rules.brackets[left.type]
            left, right, regions, nobracket = self.run_plugin(bracket.name, left, right, regions)
            if nobracket:
                return True

        # Matched brackets
        if left is not None and right is not None and bracket is not None:
            self.regions.save_complete_regions(left, right, regions, self.bracket_style, HIGH_VISIBILITY)
            return True
        return False

    def find_scopes(self, sel, adj_dir=bh_search.BH_ADJACENT_LEFT):
        """
        Find brackets by scope definition.
        """

        # Search buffer
        left, right, bracket, sub_matched = self.match_scope_brackets(sel, adj_dir)
        if sub_matched:
            return True
        regions = [sublime.Region(sel.a, sel.b)]

        if left is not None and right is not None:
            left, right, regions, _ = self.run_plugin(bracket.name, left, right, regions)
            if left is None and right is None:
                self.regions.store_sel(regions)
                return True

        return self.regions.save_regions(left, right, regions, self.bracket_style, HIGH_VISIBILITY)

    def find_matches(self, sel):
        """
        Find bracket matches
        """

        bracket = None
        left, right, adj_scope = self.match_brackets(sel)
        if adj_scope:
            return

        regions = [sublime.Region(sel.a, sel.b)]

        if left is not None and right is not None:
            bracket = self.rules.brackets[left.type]
            left, right, regions, _ = self.run_plugin(bracket.name, left, right, regions)

        if not self.regions.save_regions(left, right, regions, self.bracket_style, HIGH_VISIBILITY):
            self.regions.store_sel(regions)

    def match_scope_brackets(self, sel, adj_dir):
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
        selected_scope = None
        bracket = None
        adjusted_center = center

        # Cannot be inside a bracket pair if cursor is at zero
        if center == 0:
            if not self.rules.outside_adj:
                return left, right, selected_scope, False

        for s in self.rules.scopes:
            scope = s["name"]
            # Identify if the cursor is in a scope with bracket definitions
            try:
                scope_search = self.search.new_scope_search(
                    center, before_center, scope, adj_dir
                )
            except:
                # log(str(traceback.format_exc()))
                scope_count += 1
                continue

            # Search the bracket patterns of this scope
            # to determine if this scope matches the rules.
            bracket_count = 0
            for b in s["brackets"]:
                left, right = scope_search.get_brackets(b.open, b.close, scope_count, bracket_count)
                if left is not None and not self.validate(left, bh_search.BH_SEARCH_OPEN, True):
                    left = None
                if right is not None and not self.validate(right, bh_search.BH_SEARCH_CLOSE, True):
                    right = None
                if not self.compare(left, right, scope_bracket=True):
                    left, right = None, None
                # Track partial matches.  If a full match isn't found,
                # return the first partial match at the end.
                if partial_find is None and bool(left) != bool(right):
                    partial_find = (left, right)
                    left = None
                    right = None
                if left and right:
                    adjusted_center = scope_search.adjusted_center
                    break
                bracket_count += 1
            if left and right:
                break
            scope_count += 1

        # Full match not found.  Return partial match (if any).
        if (left is None or right is None) and partial_find is not None:
            left, right = partial_find[0], partial_find[1]

        # Make sure cursor in highlighted sub group
        if (left and adjusted_center <= left.begin) or (right and adjusted_center >= right.end):
            left, right = None, None

        if left is not None:
            selected_scope = self.rules.scopes[left.scope]["name"]
        elif right is not None:
            selected_scope = self.rules.scopes[right.scope]["name"]

        if left is not None and right is not None:
            bracket = self.rules.scopes[left.scope]["brackets"][left.type]
            if bracket.sub_search:
                self.sub_search_mode = True
                self.search.set_search_window((left.begin, right.end))
                if self.sub_search(sel, scope):
                    return left, right, self.rules.brackets[left.type], True
                elif bracket.sub_search_only:
                    left, right, bracket = None, None, None

        if self.adj_only:
            left, right = self.adjacent_check(left, right, center)

        left, right = self.post_match(left, right, center, scope_bracket=True)
        return left, right, bracket, False

    def match_brackets(self, sel, scope=None):
        """
        Regex bracket matching.
        """

        center = sel.a
        left = None
        right = None
        stack = []
        bracket_search = self.search.new_bracket_search(
            center, self.sub_search_mode, scope
        )
        if self.rules.outside_adj and not bracket_search.touch_right and not self.recursive_guard:
            if self.find_scopes(sel, bh_search.BH_ADJACENT_RIGHT):
                return None, None, True
            self.sub_search_mode = False
        for o in bracket_search.get_open(bh_search.BH_SEARCH_LEFT):
            if not self.validate(o, bh_search.BH_SEARCH_OPEN):
                continue
            if len(stack) and bracket_search.is_done(bh_search.BH_SEARCH_CLOSE):
                if self.compare(o, stack[-1]):
                    stack.pop()
                    continue
            for c in bracket_search.get_close(bh_search.BH_SEARCH_LEFT):
                if not self.validate(c, bh_search.BH_SEARCH_CLOSE):
                    continue
                if o.end <= c.begin:
                    stack.append(c)
                    continue
                elif len(stack):
                    bracket_search.remember(bh_search.BH_SEARCH_CLOSE)
                    break

            if len(stack):
                b = stack.pop()
                if self.compare(o, b):
                    continue
            else:
                left = o
            break

        bracket_search.reset_end_state()
        stack = []

        # Grab each closest closing right side bracket and attempt to match it.
        # If the closing bracket cannot be matched, select it.
        for c in bracket_search.get_close(bh_search.BH_SEARCH_RIGHT):
            if not self.validate(c, bh_search.BH_SEARCH_CLOSE):
                continue
            if len(stack) and bracket_search.is_done(bh_search.BH_SEARCH_OPEN):
                if self.compare(stack[-1], c):
                    stack.pop()
                    continue
            for o in bracket_search.get_open(bh_search.BH_SEARCH_RIGHT):
                if not self.validate(o, bh_search.BH_SEARCH_OPEN):
                    continue
                if o.end <= c.begin:
                    stack.append(o)
                    continue
                else:
                    bracket_search.remember(bh_search.BH_SEARCH_OPEN)
                    break

            if len(stack):
                b = stack.pop()
                if self.compare(b, c):
                    continue
            else:
                if left is None or self.compare(left, c):
                    right = c
            break

        if self.adj_only:
            left, right = self.adjacent_check(left, right, center)

        left, right = self.post_match(left, right, center)
        return left, right, False

    def adjacent_check(self, left, right, center):
        """
        Check if bracket pair are adjacent to cursor
        """

        if left and right:
            if left.end < center < right.begin:
                left, right = None, None
        elif (left and left.end < center) or (right and center < right.begin):
            left, right = None, None
        return left, right


####################
# Commands
####################
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

    def run(self, threshold=True, lines=False, adjacent=False, no_outside_adj=False, ignore={}, plugin={}):
        # Override events
        BhEventMgr.ignore_all = True
        BhEventMgr.modified = False
        self.bh = BhCore(
            threshold,
            lines,
            adjacent,
            no_outside_adj,
            ignore,
            plugin,
            True
        )
        self.view = self.window.active_view()
        sublime.set_timeout(self.execute, 100)

    def execute(self):
        debug("Key Event")
        self.bh.match(self.view)
        BhEventMgr.ignore_all = False
        BhEventMgr.time = time()


####################
# Events
####################
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


class BhThreadMgr(object):
    """
    Object to help track when a new thread needs to be started.
    """

    restart = False


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
    view = window.active_view() if window is not None else None
    BhEventMgr.ignore_all = True
    if bh_match is not None:
        bh_match(view, BhEventMgr.type == BH_MATCH_TYPE_EDIT)
    BhEventMgr.ignore_all = False
    BhEventMgr.time = time()


def bh_loop():
    """
    Start thread that will ensure highlighting happens after a barage of events
    Initial highlight is instant, but subsequent events in close succession will
    be ignored and then accounted for with one match by this thread
    """

    while not BhThreadMgr.restart:
        if BhEventMgr.modified is True and time() - BhEventMgr.time > BhEventMgr.wait_time:
            sublime.set_timeout(bh_run, 0)
        sleep(0.5)

    if BhThreadMgr.restart:
        BhThreadMgr.restart = False
        sublime.set_timeout(lambda: thread.start_new_thread(bh_loop, ()), 0)


####################
# Loading
####################
def init_bh_match():
    """
    Initialize the match object
    """

    global bh_match
    bh_match = BhCore().match
    debug("Match object loaded.")


def plugin_loaded():
    """
    Load up uniocode table, initialize settings and match object,
    and start event loop.  Restart event loop if already loaded.
    """

    BhEventMgr.load()
    init_bh_match()
    ure.set_cache_directory(join(sublime.packages_path(), "User"), "bh")

    global HIGH_VISIBILITY
    if sublime.load_settings("bh_core.sublime-settings").get('high_visibility_enabled_by_default', False):
        HIGH_VISIBILITY = True

    if 'running_bh_loop' not in globals():
        global running_bh_loop
        running_bh_loop = True
        thread.start_new_thread(bh_loop, ())
        debug("Starting Thread")
    else:
        debug("Restarting Thread")
        BhThreadMgr.restart = True

plugin_loaded()
