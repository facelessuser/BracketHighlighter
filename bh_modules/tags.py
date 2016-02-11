"""
BracketHighlighter.

Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import re
from collections import namedtuple
import sublime
from os.path import basename, splitext

TAG_OPEN = 0
TAG_CLOSE = 1

FLAGS = re.MULTILINE | re.IGNORECASE
HTML_START = re.compile(
    r'''(?x)
    <([\w\:\.\-]+)((?:\s+[\w\-:]+(?:\s*\$?=\s*(?:"[^"]*"|'[^']*'|[^>\s]+))?)*)\s*(\/?)>
    ''',
    FLAGS
)
CFML_START = re.compile(
    r'''(?x)
    <([\w\:\.\-]+)((?:\s+[\w\-\.:]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^>\s]+))?)*|(?:(?<=cfif)|(?<=cfelseif))[^>]+)\s*(\/?)>
    ''',
    FLAGS
)
START_TAG = {
    "html": HTML_START,
    "xhtml": HTML_START,
    "cfml": CFML_START
}
END_TAG = re.compile(r'<\/([\w\:\.\-]+)[^>]*>', FLAGS)


class TagEntry(namedtuple('TagEntry', ['begin', 'end', 'name', 'self_closing', 'single'], verbose=False)):
    """Tag entry tuple."""

    def move(self, begin, end):
        """Create a new tuple from this tuple."""

        return self._replace(begin=begin, end=end)


def compare_languge(language, lang_list):
    """Check if language is found."""

    found = False
    for l in lang_list:
        if language == l.lower():
            found = True
            break
    return found


def get_tag_mode(view, tag_mode_config):
    """Get the tag mode."""

    default_mode = None
    syntax = view.settings().get('syntax')
    language = splitext(basename(syntax))[0].lower() if syntax is not None else "plain text"
    for mode in ["html", "xhtml", "cfml"]:
        if compare_languge(language, tag_mode_config.get(mode, [])):
            return mode
    return default_mode


def highlighting(view, name, style, left, right):
    """Highlight only the tag name."""
    if style == "tag":
        tag_name = '[\w\:\.\-]+'
        if left is not None:
            region = view.find(tag_name, left.begin)
            left = left.move(region.begin(), region.end())
        if right is not None:
            region = view.find(tag_name, right.begin)
            right = right.move(region.begin(), region.end())
    return left, right


def post_match(view, name, style, first, second, center, bfr, threshold):
    """
    Given two brackets, determine if they contain a tag.

    Decide whether it is an opening or closing, and then
    find its respective closing or opening.
    """

    left, right = first, second
    threshold = [0, len(bfr)] if threshold is None else threshold
    bh_settings = sublime.load_settings("bh_core.sublime-settings")
    tag_settings = sublime.load_settings("bh_tag.sublime-settings")
    tag_mode = get_tag_mode(view, tag_settings.get("tag_mode", {}))
    tag_style = tag_settings.get("tag_style", "angle")
    outside_adj = bh_settings.get("bracket_outside_adjacent", False)
    bracket_style = style

    if first is not None and tag_mode is not None:
        matcher = TagMatch(view, bfr, threshold, first, second, center, outside_adj, tag_mode)
        left, right = matcher.match()
        if not matcher.no_tag:
            bracket_style = tag_style

    return left, right, bracket_style


class TagSearch(object):
    """Searches for tags."""

    def __init__(
        self, view, bfr, window, center, pattern,
        match_type, mode, self_closing_tags, single_tags
    ):
        """Prepare tag search object."""

        self.start = int(window[0])
        self.end = int(window[1])
        self.self_closing_tags = self_closing_tags
        self.single_tags = single_tags
        self.center = center
        self.pattern = pattern
        self.match_type = match_type
        self.mode = mode
        self.bfr = bfr
        self.prev_match = None
        self.return_prev = False
        self.done = False
        self.view = view
        self.scope_exclude = sublime.load_settings("bh_tag.sublime-settings").get("tag_scope_exclude")

    def scope_check(self, pt):
        """Check if scope is good."""

        illegal_scope = False
        for exclude in self.scope_exclude:
            illegal_scope |= bool(self.view.score_selector(pt, exclude))
        return illegal_scope

    def reset_end_state(self):
        """Reset and end the current state."""

        self.done = False
        self.prev_match = None
        self.return_prev = False

    def remember(self):
        """Instruct object to return the last tag."""

        self.return_prev = True
        self.done = False

    def get_tags(self):
        """Find all the tags."""

        if self.done:
            return
        if self.return_prev:
            self.return_prev = False
            yield self.prev_match
        for m in self.pattern.finditer(self.bfr, self.start, self.end):
            name = m.group(1).lower()
            if not self.match_type:
                single = bool(m.group(3) != "")
                if not single and self.mode != 'xhtml':
                    single = name in self.single_tags
                if self.mode != 'xhtml':
                    self_closing = name in self.self_closing_tags or name.startswith("cf")
                else:
                    self_closing = False
            else:
                if self.mode != 'xhtml' and name in self.single_tags:
                    continue
                single = False
                self_closing = False
            start = m.start(0)
            end = m.end(0)
            if not self.scope_check(start):
                self.prev_match = TagEntry(start, end, name, self_closing, single)
                self.start = end
                yield self.prev_match
        self.done = True


class TagMatch(object):
    """Find a tag match."""

    def __init__(self, view, bfr, threshold, first, second, center, outside_adj, mode):
        """Prepare tag match object."""

        tag_settings = sublime.load_settings('bh_tag.sublime-settings')
        self.view = view
        self.bfr = bfr
        self.mode = mode
        self.self_closing_tags = set(tag_settings.get('self_closing_tags', []))
        self.single_tags = set(tag_settings.get('single_tags', []))
        tag, tag_type, tag_end = self.get_first_tag(first[0])
        self.left, self.right = None, None
        self.window = None
        self.no_tag = False
        if outside_adj:
            if first[0] == center:
                center += 1
            elif center == tag_end:
                center -= 1
        if tag and first[0] < center < tag_end:
            if tag.single:
                self.left = tag
                self.right = tag
            else:
                if tag_type == "open":
                    self.left = tag
                    self.window = (tag_end, len(bfr) if threshold is None else threshold[1])
                else:
                    self.right = tag
                    self.window = (0 if threshold is None else threshold[0], first[0])
        else:
            self.left = first
            self.right = second
            self.no_tag = True

    def get_first_tag(self, offset):
        """
        Check if tag region is an opening tag or closing tag.

        Return the results
        """

        tag = None
        tag_type = None
        self_closing = False
        single = False
        m = START_TAG[self.mode].match(self.bfr[offset:])
        end = None
        if m:
            name = m.group(1).lower()
            single = bool(m.group(3) != "")
            if not single and self.mode != 'xhtml':
                single = name in self.single_tags
            if self.mode == "html":
                self_closing = name in self.self_closing_tags
            elif self.mode == "cfml":
                self_closing = name in self.self_closing_tags or name.startswith("cf")
            start = m.start(0) + offset
            end = m.end(0) + offset
            tag = TagEntry(start, end, name, self_closing, single)
            tag_type = "open"
            self.center = end
        else:
            m = END_TAG.match(self.bfr[offset:])
            if m:
                name = m.group(1).lower()
                start = m.start(0) + offset
                end = m.end(0) + offset
                tag = TagEntry(start, end, name, self_closing, single)
                tag_type = "close"
                self.center = offset
        return tag, tag_type, end

    def compare_tags(self, left, right):
        """Check if tags share the same name."""

        return left.name == right.name

    def resolve_self_closing(self, stack, c):
        """Handle self closing tags."""

        found_tag = None
        b = stack[-1]
        if self.compare_tags(b, c):
            found_tag = b
            stack.pop()
        else:
            while b is not None and b.self_closing:
                stack.pop()
                if len(stack):
                    b = stack[-1]
                    if self.compare_tags(b, c):
                        found_tag = b
                        stack.pop()
                        break
                else:
                    b = None
        return found_tag

    def match(self):
        """
        Find the corresponding open or close.

        Match only if either the close or open is already found.
        """

        stack = []

        # No tags to search for
        if self.no_tag or (self.left and self.right):
            return self.left, self.right

        # Init tag matching objects
        osearch = TagSearch(
            self.view, self.bfr, self.window,
            self.center, START_TAG[self.mode],
            0, self.mode,
            self.self_closing_tags,
            self.single_tags
        )
        csearch = TagSearch(
            self.view, self.bfr, self.window,
            self.center, END_TAG,
            1, self.mode,
            self.self_closing_tags,
            self.single_tags
        )

        # Searching for opening or closing tag to match
        match_type = TAG_OPEN if self.right else TAG_CLOSE

        # Match the tags
        for c in csearch.get_tags():
            if len(stack) and osearch.done:
                if self.resolve_self_closing(stack, c):
                    continue
            for o in osearch.get_tags():
                if o.end <= c.begin:
                    if not o.single:
                        stack.append(o)
                    continue
                else:
                    osearch.remember()
                    break

            if len(stack):
                if self.resolve_self_closing(stack, c):
                    continue
            elif match_type == TAG_OPEN and not osearch.done:
                continue
            if match_type == TAG_CLOSE:
                if self.left is None or self.compare_tags(self.left, c):
                    self.right = c
                elif self.left.self_closing:
                    self.right = self.left
            break

        if match_type == TAG_OPEN:
            # Find the rest of the the unmatched left side open brackets
            # approaching the cursor if all closing brackets were matched
            # Select the most recent open bracket on the stack.
            for o in osearch.get_tags():
                if not o.single:
                    stack.append(o)
            if len(stack):
                self.left = self.resolve_self_closing(stack, self.right)
        elif self.right is None and self.left is not None and self.left.self_closing:
            # Account for the opening tag that was found being a self closing
            self.right = self.left

        return self.left, self.right
