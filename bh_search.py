import sublime
from collections import namedtuple

BH_SEARCH_LEFT = 0
BH_SEARCH_RIGHT = 1
BH_SEARCH_OPEN = 0
BH_SEARCH_CLOSE = 1


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


class BracketSearch(object):
    """
    Object that performs regex search on the view's buffer and finds brackets.
    """

    def __init__(self, bfr, window, center, pattern, outside_adj, scope_check, scope):
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
        self.bracket_sort = self.sort_brackets if not outside_adj else self.sort_brackets_adj
        self.touch_left = False
        self.touch_right = False
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

    def findall(self, window):
        """
        Find all of the brackets.
        """

        for m in self.pattern.finditer(self.bfr, int(window[0]), int(window[1])):
            g = m.lastindex
            try:
                start = m.start(g)
                end = m.end(g)
            except:
                continue

            match_type = int(not bool(g % 2))
            bracket_id = int((g / 2) - match_type)

            if not self.scope_check(start, bracket_id, self.scope):
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
