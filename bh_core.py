"""
BracketHighlighter.

Copyright (c) 2013 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import sublime
import sublime_plugin
from os.path import basename, splitext
from time import time, sleep
import threading
import traceback
import BracketHighlighter.bh_plugin as bh_plugin
import BracketHighlighter.bh_search as bh_search
import BracketHighlighter.bh_regions as bh_regions
import BracketHighlighter.bh_rules as bh_rules
import BracketHighlighter.bh_popup as bh_popup
from BracketHighlighter.bh_logging import debug, log
from BracketHighlighter import support

if 'bh_thread' not in globals():
    bh_thread = None

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
    """Bracket matching class."""

    plugin_reload = False

    ####################
    # Match Setup
    ####################
    def __init__(
        self, override_thresh=False, count_lines=False,
        adj_only=None, no_outside_adj=False, no_block_mode=False,
        ignore=None, plugin=None, keycommand=False
    ):
        """Load settings and setup reload events if settings changes."""

        if ignore is None:
            ignore = {}
        if plugin is None:
            plugin = {}

        self.settings = sublime.load_settings("bh_core.sublime-settings")
        self.keycommand = keycommand
        if not keycommand:
            self.settings.clear_on_change('reload')
            self.settings.add_on_change('reload', self.setup)
        self.setup(
            override_thresh, count_lines, adj_only,
            no_outside_adj, no_block_mode, ignore, plugin
        )

    def setup(
        self, override_thresh=False, count_lines=False, adj_only=None,
        no_outside_adj=False, no_block_mode=False, ignore=None, plugin=None
    ):
        """Initialize class settings from settings file and inputs."""

        if ignore is None:
            ignore = {}
        if plugin is None:
            plugin = {}

        # Init view params
        self.refresh_match = False
        self.last_id_view = None
        self.last_id_sel = None
        self.view_tracker = (None, None)
        self.ignore_threshold = override_thresh or bool(self.settings.get("ignore_threshold", False))
        self.adj_only = adj_only if adj_only is not None else bool(self.settings.get("match_only_adjacent", False))
        self.auto_selection_threshold = int(self.settings.get("auto_selection_threshold", 10))
        self.kill_highlight_on_threshold = bool(self.settings.get("kill_highlight_on_threshold", False))
        if no_outside_adj is None:
            no_outside_adj = self.settings.get('ignore_outside_adjacent_in_plugin', True)
        if no_block_mode is None:
            no_block_mode = self.settings.get('ignore_block_mode_in_plugin', True)
        block_cursor = self.settings.get('block_cursor_mode', False) and not no_block_mode

        # Init search object
        self.rules = bh_rules.SearchRules(
            self.settings.get("brackets", []) + self.settings.get("user_brackets", []),
            self.settings.get("scope_brackets", []) + self.settings.get("user_scope_brackets", []),
            str(self.settings.get('bracket_string_escape_mode', "string")),
            False if no_outside_adj else self.settings.get("bracket_outside_adjacent", False),
            block_cursor
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
        """Reload rules."""

        loaded_modules = self.loaded_modules.copy()

        self.rules.load_rules(
            language,
            loaded_modules
        )

    def init_match(self, num_sels):
        """Reset matching settings for the current view's syntax."""

        syntax = self.view.settings().get('syntax')
        language = splitext(basename(syntax))[0].lower() if syntax is not None else "plain text"

        self.regions.reset(self.view, num_sels)

        if language != self.view_tracker[0] or self.view.id() != self.view_tracker[1]:
            self.view_tracker = (language, self.view.id())
            self.refresh_rules(language)
            self.regions.set_show_unmatched(language)

    def unique(self, sels):
        """Check if the current selection(s) is different from the last."""

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
        """Run a bracket plugin."""

        lbracket = bh_plugin.BracketRegion(left.begin, left.end)
        rbracket = bh_plugin.BracketRegion(right.begin, right.end)
        nobracket = False

        if (
            ("__all__" in self.plugin_targets or name in self.plugin_targets) and
            self.plugin is not None and
            self.plugin.is_enabled()
        ):
            lbracket, rbracket, regions, nobracket, refresh_match = self.plugin.run_command(
                self.view, name, lbracket, rbracket, regions
            )
            left = left.move(lbracket.begin, lbracket.end) if lbracket is not None else None
            right = right.move(rbracket.begin, rbracket.end) if rbracket is not None else None
            if refresh_match:
                self.refresh_match = True
        return left, right, regions, nobracket

    def highlighting(self, left, right, scope_bracket=False):
        """
        Adjust region to highlight.

        This is done after all methods that need
        to know actual bracket region.  At this point, we no longer care about
        the actual bracket's region, and we change the highlight region to something
        completely different.
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

        if not self.rules.highlighting:
            return left, right

        if bracket.highlighting is not None:
            lbracket, rbracket = bracket.highlighting(
                self.view,
                bracket.name,
                self.bracket_style,
                bh_plugin.BracketRegion(left.begin, left.end) if left is not None else None,
                bh_plugin.BracketRegion(right.begin, right.end) if right is not None else None
            )

            if scope_bracket:
                if lbracket is not None:
                    left = bh_search.ScopeEntry(lbracket.begin, lbracket.end, bracket_scope, bracket_type)
                else:
                    left = None
                if rbracket is not None:
                    right = bh_search.ScopeEntry(rbracket.begin, rbracket.end, bracket_scope, bracket_type)
                else:
                    right = None
            else:
                if lbracket is not None:
                    left = bh_search.BracketEntry(lbracket.begin, lbracket.end, bracket_type)
                else:
                    left = None
                if rbracket is not None:
                    right = bh_search.BracketEntry(rbracket.begin, rbracket.end, bracket_type)
                else:
                    right = None
        return left, right

    def validate(self, b, bracket_type, scope_bracket=False):
        """Validate bracket."""

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
            except Exception:
                log("Plugin Bracket Find Error:\n%s" % str(traceback.format_exc()))
        return match

    def compare(self, first, second, scope_bracket=False):
        """Compare brackets.  This function allows bracket plugins to add aditional logic."""

        if scope_bracket:
            match = first is not None and second is not None
        else:
            match = first.type == second.type

        if not self.rules.check_compare:
            return match

        if match:
            if scope_bracket:
                bracket = self.rules.scopes[first.scope]["brackets"][first.type]
            else:
                bracket = self.rules.brackets[first.type]
            try:
                if bracket.compare is not None and match:
                    match = bracket.compare(
                        bracket.name,
                        bh_plugin.BracketRegion(first.begin, first.end),
                        bh_plugin.BracketRegion(second.begin, second.end),
                        self.search.get_buffer()
                    )
            except Exception:
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
                    if lbracket is not None:
                        left = bh_search.ScopeEntry(lbracket.begin, lbracket.end, bracket_scope, bracket_type)
                    else:
                        left = None
                    if rbracket is not None:
                        right = bh_search.ScopeEntry(rbracket.begin, rbracket.end, bracket_scope, bracket_type)
                    else:
                        right = None
                else:
                    if lbracket is not None:
                        left = bh_search.BracketEntry(lbracket.begin, lbracket.end, bracket_type)
                    else:
                        left = None
                    if rbracket is not None:
                        right = bh_search.BracketEntry(rbracket.begin, rbracket.end, bracket_type)
                    else:
                        right = None
            except Exception:
                log("Plugin Post Match Error:\n%s" % str(traceback.format_exc()))

        return left, right

    ####################
    # Matching
    ####################
    def match(self, view, force_match=True):
        """Preform matching brackets surround the selection(s)."""

        if view is None:
            return

        # Ensure nothing else calls BH until done
        view.settings().set("bracket_highlighter.busy", True)

        # Abort if disabled
        if not GLOBAL_ENABLE:
            for region_key in view.settings().get("bracket_highlighter.regions", []):
                view.erase_regions(region_key)
            view.settings().set('bracket_highlighter.locations', [])
            view.settings().set("bracket_highlighter.busy", False)
            return

        # Handle key command quirks
        if self.keycommand:
            BhCore.plugin_reload = True

        if not self.keycommand and BhCore.plugin_reload:
            self.setup()
            BhCore.plugin_reload = False

        # Setup view
        self.view = view
        self.refresh_match = False
        sels = view.sel()
        num_sels = len(sels)

        # Abort if selections are beyond the threshold and "kill" is enabled
        if not self.ignore_threshold and self.kill_highlight_on_threshold:
            if self.use_selection_threshold and num_sels > self.auto_selection_threshold:
                self.regions.reset(view, num_sels)
                self.regions.highlight(HIGH_VISIBILITY)
                view.settings().set("bracket_highlighter.busy", False)
                return

        # Initialize
        if self.unique(sels) or force_match:
            # Prepare for match
            self.init_match(num_sels)

            # Nothing to search for
            if not self.rules.enabled:
                view.settings().set("bracket_highlighter.busy", False)
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

        # Setup thread to do another match to refresh the match
        if self.refresh_match:
            bh_thread.type = BH_MATCH_TYPE_SELECTION
            bh_thread.modified = True
            bh_thread.time = time()

        view.settings().set("bracket_highlighter.busy", False)

    def sub_search(self, sel, scope=None):
        """Search a scope bracket match for bracekts within."""

        # Protect against recursive search of scopes
        self.recursive_guard = True

        # Find brackets inside scope
        bracket = None
        left, right = self.match_brackets(sel, scope)[:2]

        regions = [sublime.Region(sel.a, sel.b)]

        if left is not None and right is not None:
            bracket = self.rules.brackets[left.type]
            left, right, regions, nobracket = self.run_plugin(bracket.name, left, right, regions)
            if nobracket:
                return True

        # Matched brackets
        if left is not None and right is not None and bracket is not None and not HIGH_VISIBILITY:
            left, right = self.highlighting(left, right)
            self.regions.save_complete_regions(left, right, regions, self.bracket_style, HIGH_VISIBILITY)
            return True
        return False

    def find_scopes(self, sel, adj_dir=bh_search.BH_ADJACENT_LEFT):
        """Find brackets by scope definition."""

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

        if not HIGH_VISIBILITY:
            left, right = self.highlighting(left, right, scope_bracket=True)

        return self.regions.save_regions(left, right, regions, self.bracket_style, HIGH_VISIBILITY)

    def find_matches(self, sel):
        """Find bracket matches."""

        bracket = None
        left, right, adj_scope = self.match_brackets(sel)
        if adj_scope:
            return

        regions = [sublime.Region(sel.a, sel.b)]

        if left is not None and right is not None:
            bracket = self.rules.brackets[left.type]
            left, right, regions, _ = self.run_plugin(bracket.name, left, right, regions)

        if not HIGH_VISIBILITY:
            left, right = self.highlighting(left, right)

        if not self.regions.save_regions(left, right, regions, self.bracket_style, HIGH_VISIBILITY):
            self.regions.store_sel(regions)

    def match_scope_brackets(self, sel, adj_dir):
        """
        Perform match for scope brackets.

        See if scope should be searched, and then check
        endcaps to determine if valid scope bracket.
        """

        center = sel.b
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
            if not self.rules.outside_adj and not self.rules.block_cursor:
                return left, right, selected_scope, False

        for s in self.rules.scopes:
            scope = s["name"]
            # Identify if the cursor is in a scope with bracket definitions
            try:
                scope_search = self.search.new_scope_search(
                    center, before_center, scope, adj_dir
                )
            except Exception:
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
        if self.rules.block_cursor:
            if (
                (left and center < left.begin and adjusted_center <= left.begin) or
                (right and center >= right.end and adjusted_center >= right.end)
            ):
                left, right = None, None
        elif self.rules.outside_adj:
            if (
                (left and center <= left.begin and adjusted_center <= left.begin) or
                (right and center >= right.end and adjusted_center >= right.end)
            ):
                left, right = None, None
        else:
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
            if self.rules.block_cursor:
                left, right = self.block_adjacent_check(left, right, center)
            else:
                left, right = self.adjacent_check(left, right, center)

        left, right = self.post_match(left, right, center, scope_bracket=True)
        return left, right, bracket, False

    def match_brackets(self, sel, scope=None):
        """Regex bracket matching."""

        center = sel.b
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
            if self.rules.block_cursor:
                left, right = self.block_adjacent_check(left, right, center)
            else:
                left, right = self.adjacent_check(left, right, center)

        left, right = self.post_match(left, right, center)
        return left, right, False

    def adjacent_check(self, left, right, center):
        """Check if bracket pair are adjacent to cursor."""

        if left and right:
            if left.end < center < right.begin:
                left, right = None, None
        elif (left and left.end < center) or (right and center < right.begin):
            left, right = None, None
        return left, right

    def block_adjacent_check(self, left, right, center):
        """Check if block bracket pair have the cursor directly on a bracket."""

        if left and right:
            if left.begin < center < right.begin:
                left, right = None, None
        elif (left and left.begin < center) or (right and center < right.begin):
            left, right = None, None
        return left, right


####################
# Commands
####################
class BhToggleStringEscapeModeCommand(sublime_plugin.TextCommand):
    """Toggle between regex escape and string escape for brackets in strings."""

    def run(self, edit):
        """Perform string escape toggling."""

        default_mode = sublime.load_settings("bh_core.sublime-settings").get('bracket_string_escape_mode', 'string')
        if self.view.settings().get('bracket_highlighter.bracket_string_escape_mode', default_mode) == "regex":
            self.view.settings().set('bracket_highlighter.bracket_string_escape_mode', "string")
            sublime.status_message("Bracket String Escape Mode: string")
        else:
            self.view.settings().set('bracket_highlighter.bracket_string_escape_mode', "regex")
            sublime.status_message("Bracket String Escape Mode: regex")


class BhShowStringEscapeModeCommand(sublime_plugin.TextCommand):
    """Shoe current string escape mode for sub brackets in strings."""

    def run(self, edit):
        """Show bracket string escape mode."""

        default_mode = sublime.load_settings(
            "BracketHighlighter.sublime-settings"
        ).get('bracket_string_escape_mode', 'string')
        sublime.status_message(
            "Bracket String Escape Mode: %s" % self.view.settings().get(
                'bracket_highlighter.bracket_string_escape_mode',
                default_mode
            )
        )


class BhOffscreenPopupCommand(sublime_plugin.TextCommand):
    """Command to manually show offscreen popup."""

    def run(self, edit, point=None, no_threshold=False):
        """Force popup."""

        # Find other bracket
        region = None
        index = None
        unmatched = False
        between = None

        # Ensure only 1 point is set
        if point is not None:
            sels = self.view.sel()
            sels.clear()
            sels.add(sublime.Region(point))

        # Search with no threshold
        if no_threshold:
            self.view.run_command("bh_key", {"lines": True})

        # Get point if not specified
        if point is None:
            sels = self.view.sel()
            if len(sels) == 1 and sels[0].size() == 0:
                point = sels[0].begin()

        # Get relative bracket regions for point
        if point is not None:
            locations = self.view.settings().get('bracket_highlighter.locations', {})
            for k, v in locations.get('unmatched', {}).items():
                if v[0] <= point <= v[1]:
                    unmatched = True
                    break
            if not unmatched:
                for k, v in locations.get('open', {}).items():
                    if v[0] <= point <= v[1]:
                        index = k
                        between = None
                        break
                    elif v[0] <= point <= locations.get('close', {}).get(k)[1]:
                        between = k

                if index is None:
                    for k, v in locations.get('close', {}).items():
                        if v[0] <= point <= v[1]:
                            index = k
                            between = None
                            break
                    if index is not None:
                        region = locations.get('open', {}).get(index)
                        icon = locations.get('icon', {}).get(index)
                else:
                    region = locations.get('close', {}).get(index)
                    icon = locations.get('icon', {}).get(index)

            if between:
                region = locations.get('open', {}).get(between)
                region2 = locations.get('close', {}).get(between)
                icon = locations.get('icon', {}).get(between)
                bh_popup.BhOffscreenPopup().show_popup_between(self.view, point, region, region2, icon)
            elif region is not None:
                bh_popup.BhOffscreenPopup().show_popup(self.view, point, region, icon)
            elif not no_threshold:
                bh_popup.BhOffscreenPopup().show_unmatched_popup(self.view, point)

    def is_enabled(self):
        """Check if enabled."""

        return bh_popup.HOVER_SUPPORT

    is_visible = is_enabled


class BhToggleHighVisibilityCommand(sublime_plugin.ApplicationCommand):
    """
    Toggle high visibility mode.

    Toggle a high visibility mode that
    highlights the entire bracket extent.
    """

    def run(self):
        """Toggle high visibility."""

        global HIGH_VISIBILITY
        HIGH_VISIBILITY = not HIGH_VISIBILITY


class BhToggleEnableCommand(sublime_plugin.ApplicationCommand):
    """Toggle global enable for BracketHighlighter."""

    def run(self):
        """Toggle BH enable state."""

        global GLOBAL_ENABLE
        GLOBAL_ENABLE = not GLOBAL_ENABLE
        if not GLOBAL_ENABLE:
            bh_regions.clear_all_regions()


class BhKeyCommand(sublime_plugin.TextCommand):
    """
    Command to process shortcuts, menu calls, and command palette calls.

    This is how BhCore is called with different options.
    """

    def run(
        self, edit, threshold=True, lines=False, adjacent=False,
        no_outside_adj=False, no_block_mode=False, ignore=None, plugin=None
    ):
        """Run BH key command."""

        if ignore is None:
            ignore = {}
        if plugin is None:
            plugin = {}

        # Override events
        bh_thread.ignore_all = True
        bh_thread.modified = False
        self.bh = BhCore(
            threshold,
            lines,
            adjacent,
            no_outside_adj,
            no_block_mode,
            ignore,
            plugin,
            True
        )
        self.execute()

    def execute(self):
        """Trigger actual BH command."""

        debug("Key Event")
        self.bh.match(self.view)
        bh_thread.ignore_all = False
        bh_thread.time = time()

    def is_enabled(self, **kwargs):
        """Check if command is enabled."""

        settings = self.view.settings()
        return bool(
            not settings.get('bracket_highlighter.ignore', False) and
            (
                not settings.get('is_widget') or
                sublime.load_settings("bh_core.sublime-settings").get('search_in_widgets', False)
            )
        )


class BhAsyncKeyCommand(BhKeyCommand):
    """Call BH key command asynchronously."""

    def execute(self):
        """Call execute command asynchronously."""

        sublime.set_timeout(self.async_execute, 100)

    def async_execute(self):
        """Trigger actual BH command."""

        debug("Async Key Event")
        self.bh.match(self.view)
        bh_thread.ignore_all = False
        bh_thread.time = time()


####################
# Debug
####################
class BhDebugCommand(sublime_plugin.ApplicationCommand):
    """Toggle debug commands."""

    def run(self, set_value=None):
        """Perform debug toggle."""

        settings = sublime.load_settings("bh_core.sublime-settings")
        if set_value is None:
            value = bool(settings.get("debug_enable", False))
            settings.set("debug_enable", not value)
        else:
            settings.set("debug_enable", set_value)

    def is_checked(self):
        """Check if command should be checked in menu."""

        return sublime.load_settings("bh_core.sublime-settings").get('debug_enable', False)

    def is_enabled(self, set_value=None):
        """Check if command should be enabled."""

        if set_value is None:
            enabled = True
        elif set_value:
            enabled = not sublime.load_settings("bh_core.sublime-settings").get('debug_enable', False)
        else:
            enabled = sublime.load_settings("bh_core.sublime-settings").get('debug_enable', False)
        return enabled


####################
# Events
####################
class BhListenerCommand(sublime_plugin.EventListener):
    """
    Manage when to kick off bracket matching.

    Try and reduce redundant requests by letting the
    background thread ensure certain needed match occurs
    """

    def on_hover(self, view, point, hover_zone):
        """Show popup indicating where other offscreen bracket is located."""
        settings = sublime.load_settings('bh_core.sublime-settings')
        if bh_popup.HOVER_SUPPORT and settings.get('show_offscreen_bracket_popup', True):
            # Find other bracket
            region = None
            index = None
            unmatched = False
            if hover_zone == sublime.HOVER_TEXT:
                locations = view.settings().get('bracket_highlighter.locations', {})
                for k, v in locations.get('unmatched', {}).items():
                    if v[0] <= point <= v[1]:
                        unmatched = True
                        break
                if not unmatched:
                    for k, v in locations.get('open', {}).items():
                        if v[0] <= point <= v[1]:
                            index = k
                            break
                    if index is None:
                        for k, v in locations.get('close', {}).items():
                            if v[0] <= point <= v[1]:
                                index = k
                                break
                        if index is not None:
                            region = locations.get('open', {}).get(index)
                            icon = locations.get('icon', {}).get(index)
                    else:
                        region = locations.get('close', {}).get(index)
                        icon = locations.get('icon', {}).get(index)

            # Show other bracket text
            if unmatched:
                bh_popup.BhOffscreenPopup().show_unmatched_popup(view, point)
            elif region is not None:
                bh_popup.BhOffscreenPopup().show_popup(view, point, region, icon)

    def on_load(self, view):
        """Search brackets on view load."""

        if self.ignore_event(view):
            return
        bh_thread.type = BH_MATCH_TYPE_SELECTION
        bh_thread.view = view
        sublime.set_timeout(bh_thread.payload, 0)

    def on_modified(self, view):
        """Update highlighted brackets when the text changes."""

        if self.ignore_event(view):
            return
        bh_thread.type = BH_MATCH_TYPE_EDIT
        bh_thread.modified = True
        bh_thread.view = view
        bh_thread.time = time()

    def clear_disabled(self, view):
        """Clear disabled regions."""

        settings = view.settings()
        disabled = (
            (
                settings.get('is_widget') and
                not sublime.load_settings("bh_core.sublime-settings").get('search_in_widgets', False)
            ) or
            settings.get('bracket_highlighter.ignore', False)
        )
        if disabled and settings.get('bracket_highlighter.regions'):
            for region_key in view.settings().get("bracket_highlighter.regions", []):
                view.erase_regions(region_key)
            view.settings().set('bracket_highlighter.locations', [])

    def on_activated(self, view):
        """Highlight brackets when the view gains focus again."""

        self.clear_disabled(view)

        if self.ignore_event(view):
            return
        bh_thread.type = BH_MATCH_TYPE_SELECTION
        bh_thread.view = view
        sublime.set_timeout(bh_thread.payload, 0)

    def on_selection_modified(self, view):
        """Highlight brackets when the selections change."""

        if self.ignore_event(view):
            return
        if bh_thread.type != BH_MATCH_TYPE_EDIT:
            bh_thread.type = BH_MATCH_TYPE_SELECTION
        now = time()
        bh_thread.view = view
        if now - bh_thread.time > bh_thread.wait_time:
            sublime.set_timeout(bh_thread.payload, 0)
        else:
            bh_thread.modified = True
            bh_thread.time = now

    def ignore_event(self, view):
        """
        Ignore highlight request.

        Ignore request to highlight if the view is a widget,
        or if it is too soon to accept an event.
        """

        settings = view.settings()
        return (
            bh_thread.ignore_all or
            settings.get('bracket_highlighter.ignore', False) or
            (
                settings.get('is_widget') and
                not sublime.load_settings("bh_core.sublime-settings").get('search_in_widgets', False)
            )
        )


class BhThread(threading.Thread):
    """BH threading."""

    def __init__(self):
        """Setup the thread."""

        self.reset()
        self.view = None
        threading.Thread.__init__(self)

    def reset(self):
        """Reset the thread variables."""

        self.wait_time = 0.12
        self.time = time()
        self.modified = False
        self.type = BH_MATCH_TYPE_SELECTION
        self.ignore_all = False
        self.abort = False

    def payload(self):
        """Code to run."""

        self.modified = False
        self.ignore_all = True
        if bh_match is not None:
            bh_match(self.view, self.type == BH_MATCH_TYPE_EDIT)
        self.view = None
        self.ignore_all = False
        self.time = time()

    def kill(self):
        """Kill thread."""

        self.abort = True
        while self.is_alive():
            pass
        self.reset()

    def run(self):
        """Thread loop."""

        while not self.abort:
            if self.modified is True and time() - self.time > self.wait_time:
                sublime.set_timeout(self.payload, 0)
            sleep(0.5)


####################
# Loading
####################
def init_bh_match():
    """Initialize the match object."""

    global bh_match
    bh_match = BhCore().match
    debug("Match object loaded.")


def plugin_loaded():
    """
    General plugin initialization.

    Load up uniocode table, initialize settings and match object,
    and start event loop.  Restart event loop if already loaded.
    """

    global HIGH_VISIBILITY
    global bh_thread

    settings = sublime.load_settings("bh_core.sublime-settings")

    # Try and ensure key dependencies are at the latest known good version.
    # This is only done because Package Control does not do this on package upgrade at the present.
    try:
        from package_control import events

        if bh_popup.HOVER_SUPPORT and events.post_upgrade(support.__pc_name__):
            if not bh_popup.LATEST_SUPPORTED_MDPOPUPS and settings.get('upgrade_dependencies', True):
                window = sublime.active_window()
                if window:
                    window.run_command('satisfy_dependencies')
    except ImportError:
        log('Could not import Package Control')

    init_bh_match()

    global HIGH_VISIBILITY
    if sublime.load_settings("bh_core.sublime-settings").get('high_visibility_enabled_by_default', False):
        HIGH_VISIBILITY = True

    if bh_thread is not None:
        bh_thread.kill()
    bh_thread = BhThread()
    bh_thread.start()


def plugin_unloaded():
    """Tear down plugin."""

    bh_thread.kill()
    bh_regions.clear_all_regions()
