import sublime
from collections import namedtuple
import BracketHighlighter.ure as ure


def exclude_bracket(enabled, filter_type, language_list, language):
    """
    Exclude or include brackets based on filter lists.
    """

    exclude = True
    if enabled:
        # Black list languages
        if filter_type == 'blacklist':
            exclude = False
            if language is not None:
                for item in language_list:
                    if language == item.lower():
                        exclude = True
                        break
        # White list languages
        elif filter_type == 'whitelist':
            if language is not None:
                for item in language_list:
                    if language == item.lower():
                        exclude = False
                        break
    return exclude


def is_valid_definition(params, language):
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


class BracketSearchType(object):
    """
    Userful structure to specify bracket matching direction.
    """

    opening = 0
    closing = 1


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
        self.validate = bracket.get("validate")
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
        self.sub_search = self.sub_search_only is True or sub_search == "true"
        self.compare = bracket.get("compare")
        self.post_match = bracket.get("post_match")
        self.validate = bracket.get("validate")
        self.scopes = bracket["scopes"]


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
        if (end <= self.center if match_type else start < self.center):
            # Sort bracket to left
            self.left[match_type].append(BracketEntry(start, end, bracket_id))
        elif (end > self.center if match_type else start >= self.center):
            # Sort bracket to right
            self.right[match_type].append(BracketEntry(start, end, bracket_id))

    def sort_brackets_adj(self, start, end, match_type, bracket_id):
        if (
            self.touch_right is False and
            end == (self.center)
        ):
            # Check for adjacent opening or closing bracket on left side
            entry = BracketEntry(start, end, bracket_id)
            self.touch_right = True
            if match_type == BracketSearchType.opening:
                self.left[match_type].append(entry)
            else:
                self.right[match_type].append(entry)
        elif (end <= self.center if match_type else start < self.center):
            # Sort bracket to left
            self.left[match_type].append(BracketEntry(start, end, bracket_id))
        elif (
            self.touch_right is False and
            self.touch_left is False and
            match_type == BracketSearchType.opening and
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
        Find all of the brackets and sort them
        to "left of the cursor" and "right of the cursor"
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

        for b in self._get_bracket(bracket_code, BracketSearchType.opening):
            yield b

    def get_close(self, bracket_code):
        """
        Get closing bracket.  Accepts a bracket code that
        determines which side of the cursor the next match is returned from.
        """

        for b in self._get_bracket(bracket_code, BracketSearchType.closing):
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
