import sublime
from collections import namedtuple

BH_SEARCH_LEFT = 0
BH_SEARCH_RIGHT = 1
BH_SEARCH_OPEN = 0
BH_SEARCH_CLOSE = 1
BH_ADJACENT_LEFT = 0
BH_ADJACENT_RIGHT = 1


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


class Search(object):
    """
    Search buffer object
    """

    def __init__(self, view, rules, sel, selection_threshold=None):
        """
        Read in the view's buffer for scanning for brackets etc.
        """

        self.rules = rules

        self.view = view
        # Determine how much of the buffer to search
        view_min = 0
        view_max = view.size()
        if selection_threshold is not None:
            left_delta = sel.a - view_min
            right_delta = view_max - sel.a
            limit = selection_threshold / 2
            rpad = limit - left_delta if left_delta < limit else 0
            lpad = limit - right_delta if right_delta < limit else 0
            llimit = limit + lpad
            rlimit = limit + rpad
            search_window = (
                sel.a - llimit if left_delta >= llimit else view_min,
                sel.a + rlimit if right_delta >= rlimit else view_max
            )
        else:
            search_window = (0, view_max)

        # Search Buffer
        self.bfr = view.substr(sublime.Region(0, view_max))
        self.set_search_window(search_window)

    def get_buffer(self):
        """
        Get view buffer
        """

        return self.bfr

    def set_search_window(self, search_window):
        """
        Set the window of search in the buffer
        """

        self.search_window = search_window

    def new_scope_search(self, center, before_center, scope, adj_dir):
        return ScopeSearch(
            self, center, before_center, scope, adj_dir
        )

    def new_bracket_search(self, center, subsearch, scope):
        return BracketSearch(self, center, subsearch, scope)


class ScopeSearch(object):
    """
    Object that extracts brackets from scope
    """

    def __init__(self, search, center, before_center, scope, adj_dir):
        """
        Set scope buffer by getting the extent of the scope
        """

        self.adjusted_center = center
        self.view = search.view
        self.search = search
        extent = None

        if self.is_scope(center, before_center, scope, adj_dir):
            max_size = self.view.size() - 1
            extent = self.view.extract_scope(self.adjusted_center)
            while extent is not None and extent.begin() != 0:
                if search.view.match_selector(extent.begin() - 1, scope):
                    extent = extent.cover(self.view.extract_scope(extent.begin() - 1))
                    if extent.begin() < search.search_window[0] or extent.end() > search.search_window[1]:
                        extent = None
                else:
                    break
            while extent is not None and extent.end() != max_size:
                if self.view.match_selector(extent.end(), scope):
                    extent = extent.cover(self.view.extract_scope(extent.end()))
                    if extent.begin() < search.search_window[0] or extent.end() > search.search_window[1]:
                        extent = None
                else:
                    break
        assert extent is not None, "Failed to acquire scope buffer!"

        self.extent = extent
        self.scope_bfr = search.get_buffer()[extent.begin():extent.end()]

    def is_scope(self, center, before_center, scope, adj_dir=None):
        """
        Check if cursor is in scope or touching scope
        """

        match = False
        if before_center > 0:
            match = (
                self.view.match_selector(center, scope) and
                self.view.match_selector(before_center, scope)
            )
        if not match and True and self.search.rules.outside_adj:
            if adj_dir == BH_ADJACENT_LEFT:
                if before_center > 0:
                    match = self.view.match_selector(before_center, scope)
                    if match:
                        self.adjusted_center = before_center
            else:
                match = self.view.match_selector(center, scope)
                if match:
                    self.adjusted_center += 1
        return match

    def get_brackets(self, open_pattern, close_pattern, scope_id, bracket_id):
        """
        Get the brackets from the scopes endpoints using
        the given open and closing patterns
        """

        o = None
        c = None
        m = open_pattern.search(self.scope_bfr)
        if m and m.group(1):
            o = ScopeEntry(self.extent.begin() + m.start(1), self.extent.begin() + m.end(1), scope_id, bracket_id)
        m = close_pattern.search(self.scope_bfr)
        if m and m.group(1):
            c = ScopeEntry(self.extent.begin() + m.start(1), self.extent.begin() + m.end(1), scope_id, bracket_id)
        return o, c


class BracketSearch(object):
    """
    Object that performs regex search on the view's buffer and finds brackets.
    """

    def __init__(self, search, center, sub_search, scope):
        """
        Prepare for search
        """

        self.search = search
        self.center = center
        self.scope = scope
        self.sub_search = sub_search
        if sub_search:
            self.pattern = search.rules.sub_pattern
        else:
            self.pattern = search.rules.pattern
        if search.rules.outside_adj:
            self.bracket_sort = self.sort_brackets_adj
        else:
            self.bracket_sort = self.sort_brackets
        self.prev_match = [None, None]
        self.return_prev = [False, False]
        self.done = [False, False]
        self.start = [None, None]
        self.left = [[], []]
        self.right = [[], []]
        self.touch_left = False
        self.touch_right = False
        self.findall()

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
        Check if bracket follows escape characters.
        Account for if in string or regex string scope.
        """

        escaped = False
        start = pt - 1
        first = False
        if (
            self.search.view.settings().get(
                "bracket_string_escape_mode", self.search.rules.string_escape_mode
            ) == "string"
        ):
            first = True
        while self.search.view.substr(start) == "\\":
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

        bracket = self.search.rules.brackets[bracket_id]
        if self.sub_search and not bracket.find_in_sub_search:
            return True
        illegal_scope = False
        # Scope sent in, so we must be scanning whatever this scope is
        if scope is not None:
            if self.escaped(pt, bracket.ignore_string_escape, scope):
                illegal_scope = True
            return illegal_scope
        # for exception in bracket.scope_exclude_exceptions:
        elif len(bracket.scope_exclude_exceptions) and self.search.view.match_selector(pt, ", ".join(bracket.scope_exclude_exceptions)):
            pass
        elif len(bracket.scope_exclude) and self.search.view.match_selector(pt, ", ".join(bracket.scope_exclude)):
            illegal_scope = True
        return illegal_scope

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

    def sort_brackets(self, start, end, match_type, bracket_id):
        """
        Sort brackets by type (opening or closing) and whether they
        are left of cursor or right.
        """

        if (end <= self.center if match_type else start < self.center):
            # Sort bracket to left
            self.left[match_type].append(BracketEntry(start, end, bracket_id))
        elif (end > self.center if match_type else start >= self.center):
            # Sort bracket to right
            self.right[match_type].append(BracketEntry(start, end, bracket_id))

    def sort_brackets_adj(self, start, end, match_type, bracket_id):
        """
        Sort brackets but with slightly altered logic for telling when
        there are brackets adjacent to the cursor.
        """

        if (
            self.touch_right is False and
            end == (self.center)
        ):
            # Check for adjacent opening or closing bracket on left side
            entry = BracketEntry(start, end, bracket_id)
            self.touch_right = True
            if match_type == BH_SEARCH_OPEN:
                self.left[match_type].append(entry)
            else:
                self.right[match_type].append(entry)
        elif (end <= self.center if match_type else start < self.center):
            # Sort bracket to left
            self.left[match_type].append(BracketEntry(start, end, bracket_id))
        elif (
            self.touch_right is False and
            self.touch_left is False and
            match_type == BH_SEARCH_OPEN and
            start == self.center
        ):
            # Check for adjacent opening bracket of right
            entry = BracketEntry(start, end, bracket_id)
            self.touch_left = entry
            self.left[match_type].append(entry)
        elif (end > self.center if match_type else start >= self.center):
            # Sort bracket to right
            self.right[match_type].append(BracketEntry(start, end, bracket_id))

    def findall(self):
        """
        Find all of the brackets.
        """

        for m in self.pattern.finditer(self.search.get_buffer(), int(self.search.search_window[0]), int(self.search.search_window[1])):
            g = m.lastindex
            try:
                start = m.start(g)
                end = m.end(g)
            except:
                continue

            match_type = int(not bool(g % 2))
            bracket_id = int((g / 2) - match_type)

            if not self.is_illegal_scope(start, bracket_id, self.scope):
                self.bracket_sort(start, end, match_type, bracket_id)

    def get_open(self, bracket_code):
        """
        Get opening bracket.  Accepts a bracket code that
        determines which side of the cursor the next match is returned from.
        """

        for b in self._get_bracket(bracket_code, BH_SEARCH_OPEN):
            yield b

    def get_close(self, bracket_code):
        """
        Get closing bracket.  Accepts a bracket code that
        determines which side of the cursor the next match is returned from.
        """

        for b in self._get_bracket(bracket_code, BH_SEARCH_CLOSE):
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
        if bracket_code == BH_SEARCH_LEFT:
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
