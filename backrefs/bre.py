r"""
Backrefs re.

Add the ability to use the following backrefs with re:

    * \l             - Lowercase character class (search)
    * \c             - Uppercase character class (search)
    * \L             - Inverse of lowercase character class (search)
    * \C             - Inverse of uppercase character class (search)
    * \Q and \Q...\E - Escape/quote chars (search)
    * \c and \C...\E - Uppercase char or chars (replace)
    * \l and \L...\E - Lowercase char or chars (replace)
    * \p{Lu} and \p{Letter} and \p{Uppercase_Letter} - Unicode properties (search unicode)
    * \P{Lu} adn \P{Letter} and \P{Uppercase_Letter} - Inverse Unicode properties (search unicode)

Note
=========
- Only category or category with subcategory can be specifed for \p or \P.

  So the following is okay: r"[\p{Lu}\p{Ll}]" or r"[\p{L}]" etc.
  The following is *not* okay: r"[\p{Lul}]" or r"[\p{Lu Ll}]" etc.

- Your search pattern must be a unicode string in order to use unicode proptery backreferences,
  but you do *not* have to use re.UNICODE.

- \l, \L, \c, and \C in searches will be ascii ranges unless re.UNICODE is used.  This is to
  give some consistency with re's \w, \W, \b, \B, \d, \D, \s and \S.

Compiling
=========
pattern = compile_search(r'somepattern', flags)
replace = compile_replace(pattern, r'\1 some replace pattern')

Usage
=========
Recommended to use compiling.  Assuming the above compiling:

    text = pattern.sub(replace, 'sometext')

--or--

    m = pattern.match('sometext')
    if m:
        text = replace(m)  # similar to m.expand(template)

Licensed under MIT
Copyright (c) 2011 - 2015 Isaac Muse <isaacmuse@gmail.com>
"""
from __future__ import unicode_literals
import sre_parse
import functools
import re
from . import common_tokens as ctok
from . import compat
from . import uniprops

# Expose some common re flags and methods to
# save having to import re and backrefs libs
DEBUG = re.DEBUG
I = re.I
IGNORECASE = re.IGNORECASE
L = re.L
LOCALE = re.LOCALE
M = re.M
MULTILINE = re.MULTILINE
S = re.S
DOTALL = re.DOTALL
U = re.U
UNICODE = re.UNICODE
X = re.X
VERBOSE = re.VERBOSE
if compat.PY3:
    A = re.A
    ASCII = re.ASCII
escape = re.escape
purge = re.purge

RE_TYPE = type(re.compile('', 0))

# Case upper or lower
_UPPER = 0
_LOWER = 1

# Mapping of friendly unicode category names to shorthand codes.
unicode_property_map = {
    # Other
    "Other": "C",
    "Control": "Cc",
    "Format": "Cf",
    "Surrogate": "Cs",
    "Private_Use": "Co",
    "Unassigned": "Cn",

    # Letter
    "Letter": "L",
    "Uppercase_Letter": "Lu",
    "Lowercase_Letter": "Ll",
    "Titlecase_Letter": "Lt",
    "Modifier_Letter": "Lm",
    "Other_Letter": "Lo",

    # Mark
    "Mark": "M",
    "Nonspacing_Mark": "Mc",
    "Spacing_Mark": "Me",
    "Enclosing_Mark": "Md",

    # Number
    "Number": "N",
    "Decimal_Number": "Nd",
    "Letter_Number": "Nl",
    "Other_Number": "No",

    # Punctuation
    "Punctuation": "P",
    "Connector_Punctuation": "Pc",
    "Dash_Punctuation": "Pd",
    "Open_Punctuation": "Ps",
    "Close_Punctuation": "Pe",
    "Initial_Punctuation": "Pi",
    "Final_Punctuation": "Pf",
    "Other_Punctuation": "Po",

    # Symbol
    "Symbol": "S",
    "Math_Symbol": "Sm",
    "Currency_Symbol": "Sc",
    "Modifier_Symbol": "Sk",
    "Other_Symbol": "So",

    # Separator
    "Separator": "Z",
    "Space_Separator": "Zs",
    "Line_Separator": "Zl",
    "Paragraph_Separator": "Zp"
}

# Regex pattern for unicode properties
_UPROP = r'''
(?:p|P)\{
(?:
    C(?:c|f|s|o|n)?|L(?:u|l|t|m|o|n)?|M(?:n|c|e|d)?|N(?:d|l|o|c|d)?|
    P(?:c|d|s|e|i|f|o)?|S(?:c|m|k|o)?|Z(?:p|s|l)?|
    Letter|Uppercase_Letter|Lowercase_Letter|Titlecase_Letter|Modifier_Letter|Other_Letter|
    Mark|Nonspacing_Mark|Spacing_Mark|Enclosing_Mark|
    Number|Decimal_Number|Letter_Number|Other_Number|
    Punctuation|Connector_Punctuation|Dash_Punctuation|Open_Punctuation|Close_Punctuation|
    Initial_Punctuation|Final_Punctuation|Other_Punctuation|
    Symbol|Math_Symbol|Currency_Symbol|Modifier_Symbol|Other_Symbol|
    Separator|Space_Separator|Line_Separator|Paragraph_Separator|
    Control|Format|Surrogate|Private_Use|Unassigned
)
\}
'''

# Unicode string related references
utokens = {
    "uni_prop": "p",
    "inverse_uni_prop": "P",
    "ascii_low_props": 'a-z',
    "ascii_upper_props": 'A-Z',
    "negative_lower": '\u0000-\u0060\u007b-\u007f',
    "negative_upper": '\u0000-\u0040\u005b-\u007f',
    "re_search_ref": re.compile(
        r'''(?x)
        (\\)+
        (
            [lLcCEQ] |
            %(uni_prop)s
        )? |
        (
            [lLcCEQ] |
            %(uni_prop)s
        )
        ''' % {"uni_prop": _UPROP}
    ),
    "re_search_ref_verbose": re.compile(
        r'''(?x)
        (\\)+
        (
            [lLcCEQ#] |
            %(uni_prop)s
        )? |
        (
            [lLcCEQ#] |
            %(uni_prop)s
        )
        ''' % {"uni_prop": _UPROP}
    ),
    "re_flags": re.compile(
        r'(?s)(\\.)|\(\?([aiLmsux]+)\)|(.)' if compat.PY3 else r'(?s)(\\.)|\(\?([iLmsux]+)\)|(.)'
    ),
    "ascii_flag": "a"
}

# Byte string related references
btokens = {
    "def_back_ref": set(
        [
            b"a", b"b", b"f", b"n", b"r",
            b"t", b"v", b"A", b"b", b"B",
            b"d", b"D", b"s", b"S", b"w",
            b"W", b"Z", b"u", b"x", b"g"
        ]
    ),
    "uni_prop": b"p",
    "inverse_uni_prop": b"P",
    "ascii_low_props": b'a-z',
    "ascii_upper_props": b'A-Z',
    "negative_lower": b'\x00-\x60\x7b-\x7f',
    "negative_upper": b'\x00-\x40\x5b-\x7f',
    "re_search_ref": re.compile(
        br'''(?x)
        (\\)+
        (
            [lLcCEQ]
        )? |
        (
            [lLcCEQ]
        )
        '''
    ),
    "re_search_ref_verbose": re.compile(
        br'''(?x)
        (\\)+
        (
            [lLcCEQ#]
        )? |
        (
            [lLcCEQ#]
        )
        '''
    ),
    "re_flags": re.compile(
        br'(?s)(\\.)|\(\?([aiLmsux]+)\)|(.)' if compat.PY3 else br'(?s)(\\.)|\(\?([iLmsux]+)\)|(.)'
    ),
    "ascii_flag": b"a"
}


def _get_unicode_category(prop, negate=False):
    """Retrieve the unicode category from the table."""

    if not negate:
        p1, p2 = (prop[0], prop[1]) if len(prop) > 1 else (prop[0], None)
        return ''.join(
            [v for k, v in uniprops.unicode_properties.get(p1, {}).items() if not k.startswith('^')]
        ) if p2 is None else uniprops.unicode_properties.get(p1, {}).get(p2, '')
    else:
        p1, p2 = (prop[0], prop[1]) if len(prop) > 1 else (prop[0], '')
        return uniprops.unicode_properties.get(p1, {}).get('^' + p2, '')


# Break apart template patterns into char tokens
class ReplaceTokens(compat.Tokens):
    """Tokens."""

    def __init__(self, string, boundaries):
        """Initialize."""

        if isinstance(string, compat.binary_type):
            ctokens = ctok.btokens
        else:
            ctokens = ctok.utokens

        self.string = string
        self._b_slash = ctokens["b_slash"]
        self._re_replace_ref = ctokens["re_replace_ref"]
        self.max_index = len(string) - 1
        self.index = 0
        self.last = 0
        self.current = None
        self.boundaries = boundaries
        self.boundary = self.boundaries.pop(0) if boundaries else (self.max_index + 1, self.max_index + 1)

    def _in_boundary(self, index):
        """Check if index is in current boundary."""

        return (
            self.boundary and
            (
                self.boundary[0] <= index < self.boundary[1] or
                self.boundary[0] == index == self.boundary[1]
            )
        )

    def in_boundary(self):
        """Check if last/current index is in current boundary (public)."""
        return self._in_boundary(self.last)

    def _update_boundary(self):
        """Update to next boundary."""
        if self.boundaries:
            self.boundary = self.boundaries.pop(0)
        else:
            self.boundary = (self.max_index + 1, self.max_index + 1)

    def _out_of_boundary(self, index):
        """Return if the index has exceeded the right boundary."""

        return self.boundary is not None and index >= self.boundary[1]

    def __iter__(self):
        """Iterate."""

        return self

    def iternext(self):
        """
        Iterate through characters of the string.

        Count escaped l, L, c, C, E and backslash as a single char.
        """

        if self.index > self.max_index:
            raise StopIteration

        if self._out_of_boundary(self.index):
            self._update_boundary()

        if not self._in_boundary(self.index):
            char = self.string[self.index:self.index + 1]
            if char == self._b_slash:
                m = self._re_replace_ref.match(self.string[self.index + 1:self.boundary[0]])
                if m:
                    if m.group(1):
                        if m.group(2):
                            self.index += 1
                    else:
                        char += m.group(3)
        else:
            char = self.string[self.boundary[0]:self.boundary[1]]

        self.last = self.index
        self.index += len(char)
        self.current = char
        return self.current


class SearchTokens(compat.Tokens):
    """Tokens."""

    def __init__(self, string, verbose):
        """Initialize."""

        if isinstance(string, compat.binary_type):
            tokens = btokens
            ctokens = ctok.btokens
        else:
            tokens = utokens
            ctokens = ctok.utokens

        self.string = string
        if verbose:
            self._re_search_ref = tokens["re_search_ref_verbose"]
        else:
            self._re_search_ref = tokens["re_search_ref"]
        self._b_slash = ctokens["b_slash"]
        self.max_index = len(string) - 1
        self.index = 0
        self.current = None

    def __iter__(self):
        """Iterate."""

        return self

    def iternext(self):
        """
        Iterate through characters of the string.

        Count escaped l, L, c, C, E and backslash as a single char.
        """

        if self.index > self.max_index:
            raise StopIteration

        char = self.string[self.index:self.index + 1]
        if char == self._b_slash:
            m = self._re_search_ref.match(self.string[self.index + 1:])
            if m:
                if m.group(1):
                    char += self._b_slash
                else:
                    char += m.group(3)

        self.index += len(char)
        self.current = char
        return self.current


# Templates
class ReplaceTemplate(object):
    """Replace template."""

    def __init__(self, pattern, template):
        """Initialize."""

        if isinstance(template, compat.binary_type):
            self.binary = True
            ctokens = ctok.btokens
        else:
            self.binary = False
            ctokens = ctok.utokens

        self._original = template
        self._back_ref = set()
        self._b_slash = ctokens["b_slash"]
        self._empty = ctokens["empty"]
        self._add_back_references(ctokens["replace_tokens"])
        self._template = self._escape_template(template)
        self.parse_template(pattern)

    def parse_template(self, pattern):
        """Parse template."""
        self.groups, self.literals = sre_parse.parse_template(self._template, pattern)

    def get_base_template(self):
        """Return the unmodified template before expansion."""

        return self._original

    def _escape_template(self, template):
        """
        Escape backreferences.

        Because the new backreferences are recognized by python
        we need to escape them so they come out okay.
        """

        new_template = []
        slash_count = 0
        for c in compat.iterstring(template):
            if c == self._b_slash:
                slash_count += 1
            elif c != self._b_slash:
                if slash_count > 1 and c in self._back_ref:
                    new_template.append(self._b_slash * (slash_count - 1))
                slash_count = 0
            new_template.append(c)
        if slash_count > 1:
            # End of line slash
            new_template.append(self._b_slash * (slash_count))
            slash_count = 0
        return self._empty.join(new_template)

    def _add_back_references(self, args):
        """
        Add new backreferences.

        Only add if they don't interfere with existing ones.
        """

        for arg in args:
            if isinstance(arg, compat.binary_type if self.binary else compat.string_type) and len(arg) == 1:
                self._back_ref.add(arg)

    def get_group_index(self, index):
        """Find and return the appropriate group index."""

        g_index = None
        for group in self.groups:
            if group[0] == index:
                g_index = group[1]
                break
        return g_index


class SearchTemplate(object):
    """Search Template."""

    def __init__(self, search, re_verbose=False, re_unicode=None):
        """Initialize."""

        if isinstance(search, compat.binary_type):
            self.binary = True
            tokens = btokens
            ctokens = ctok.btokens
        else:
            self.binary = False
            tokens = utokens
            ctokens = ctok.utokens

        self._verbose_flag = ctokens["verbose_flag"]
        self._empty = ctokens["empty"]
        self._b_slash = ctokens["b_slash"]
        self._ls_bracket = ctokens["ls_bracket"]
        self._rs_bracket = ctokens["rs_bracket"]
        self._unicode_flag = ctokens["unicode_flag"]
        self._ascii_flag = tokens["ascii_flag"]
        self._esc_end = ctokens["esc_end"]
        self._end = ctokens["end"]
        self._uni_prop = tokens["uni_prop"]
        self._inverse_uni_prop = tokens["inverse_uni_prop"]
        self._ascii_low_props = tokens["ascii_low_props"]
        self._ascii_upper_props = tokens["ascii_upper_props"]
        self._lc = ctokens["lc"]
        self._lc_span = ctokens["lc_span"]
        self._uc = ctokens["uc"]
        self._uc_span = ctokens["uc_span"]
        self._quote = ctokens["quote"]
        self._negate = ctokens["negate"]
        self._negative_upper = tokens["negative_upper"]
        self._negative_lower = tokens["negative_lower"]
        self._re_flags = tokens["re_flags"]
        self._nl = ctokens["nl"]
        self._hashtag = ctokens["hashtag"]
        self.search = search
        self.groups, quotes = self.find_char_groups(search)
        self.verbose, self.unicode = self.find_flags(search, quotes, re_verbose, re_unicode)
        if self.verbose:
            self._verbose_tokens = ctokens["verbose_tokens"]
        else:
            self._verbose_tokens = tuple()
        self.extended = []

    def find_flags(self, s, quotes, re_verbose, re_unicode):
        """Find verbose and unicode flags."""

        new = []
        start = 0
        verbose_flag = bool(re_verbose)
        unicode_flag = bool(re_unicode)
        if compat.PY3:
            ascii_flag = re_unicode is not None and not re_unicode
        else:
            ascii_flag = False
        avoid = quotes + self.groups
        avoid.sort()
        if (unicode_flag or ascii_flag) and verbose_flag:
            return bool(verbose_flag), bool(unicode_flag)
        for a in avoid:
            new.append(s[start:a[0] + 1])
            start = a[1]
        new.append(s[start:])
        for m in self._re_flags.finditer(self._empty.join(new)):
            if m.group(2):
                if compat.PY3 and self._ascii_flag in m.group(2):
                    ascii_flag = True
                elif self._unicode_flag in m.group(2):
                    unicode_flag = True
                if self._verbose_flag in m.group(2):
                    verbose_flag = True
            if (unicode_flag or ascii_flag) and verbose_flag:
                break
        if compat.PY3 and not unicode_flag and not ascii_flag:
            unicode_flag = True
        return bool(verbose_flag), bool(unicode_flag)

    def find_char_groups(self, s):
        """Find character groups."""

        pos = 0
        groups = []
        quotes = []
        quote_found = False
        quote_start = 0
        escaped = False
        found = False
        first = None
        for c in compat.iterstring(s):
            if c == self._b_slash:
                escaped = not escaped
            elif escaped and not found and not quote_found and c == self._quote:
                quote_found = True
                quote_start = pos - 1
                escaped = False
            elif escaped and not found and quote_found and c == self._end:
                quotes.append((quote_start, pos))
                quote_found = False
                escaped = False
            elif escaped:
                escaped = False
            elif quote_found:
                pass
            elif c == self._ls_bracket and not found:
                found = True
                first = pos
            elif c == self._negate and found and (pos == first + 1):
                first = pos
            elif c == self._rs_bracket and found and (pos != first + 1):
                groups.append((first, pos))
                found = False
            pos += 1
        if quote_found:
            quotes.append((quote_start, pos - 1))
        return groups, quotes

    def unicode_props(self, props, in_group, negate=False):
        """Insert unicode properties."""

        if len(props) > 2:
            props = unicode_property_map.get(props, None)

        properties = []
        if props is not None:
            if not in_group:
                v = _get_unicode_category(props)
                if v is not None:
                    if negate:
                        v = self._ls_bracket + self._negate + v + self._rs_bracket
                    else:
                        v = self._ls_bracket + v + self._rs_bracket
                    properties = [v]
            else:
                v = _get_unicode_category(props, negate)
                if v is not None:
                    properties = [v]
        return properties

    def ascii_props(self, case, in_group, negate=False):
        """Insert ascii (or unicode) case properties."""

        # Use traditional ASCII upper/lower case unless:
        #    1. The strings fed in are not binary
        #    2. And the the unicode flag was used
        if self.binary or not self.unicode:
            v = self._ascii_upper_props if case == _UPPER else self._ascii_low_props
            if not in_group:
                if negate:
                    v = self._ls_bracket + self._negate + v + self._rs_bracket
                else:
                    v = self._ls_bracket + v + self._rs_bracket
            elif negate:
                v = self._negative_upper if case == _UPPER else self._negative_lower
            return [v]
        else:
            return self.unicode_props('Lu' if case == _UPPER else 'Ll', in_group, negate)

    def comments(self, i):
        """Handle comments in verbose patterns."""

        parts = []
        try:
            t = next(i)
            while t != self._nl:
                parts.append(t)
                t = next(i)
            parts.append(self._nl)
        except StopIteration:
            pass
        return parts

    def quoted(self, i):
        r"""Handle quoted block."""

        quoted = []
        raw = []
        if not self.in_group(i.index - 1):
            try:
                t = next(i)
                while t != self._esc_end:
                    raw.append(t)
                    t = next(i)
            except StopIteration:
                pass
            if len(raw):
                quoted.extend([escape(self._empty.join(raw))])
        return quoted

    def in_group(self, index):
        """Check if last index was in a char group."""

        inside = False
        for g in self.groups:
            if g[0] <= index <= g[1]:
                inside = True
                break
        return inside

    def apply(self):
        """Apply search template."""

        i = SearchTokens(self.search, self.verbose)
        iter(i)

        for t in i:
            if len(t) > 1:
                # handle our stuff

                c = t[1:]

                if c.startswith(self._uni_prop):
                    self.extended.extend(self.unicode_props(c[2:-1], self.in_group(i.index - 1)))
                elif c.startswith(self._inverse_uni_prop):
                    self.extended.extend(self.unicode_props(c[2:-1], self.in_group(i.index - 1), negate=True))
                elif c == self._lc:
                    # Postpone evaluation of ASCII props as we don't yet know if unicode flag is enabled
                    self.extended.extend(self.ascii_props(_LOWER, self.in_group(i.index - 1)))
                elif c == self._lc_span:
                    # Postpone evaluation of ASCII props as we don't yet know if unicode flag is enabled
                    self.extended.extend(self.ascii_props(_LOWER, self.in_group(i.index - 1), negate=True))
                elif c == self._uc:
                    # Postpone evaluation of ASCII props as we don't yet know if unicode flag is enabled
                    self.extended.extend(self.ascii_props(_UPPER, self.in_group(i.index - 1)))
                elif c == self._uc_span:
                    # Postpone evaluation of ASCII props as we don't yet know if unicode flag is enabled
                    self.extended.extend(self.ascii_props(_UPPER, self.in_group(i.index - 1), negate=True))
                elif c[0:1] in self._verbose_tokens:
                    self.extended.append(t)
                elif c == self._quote:
                    self.extended.extend(self.quoted(i))
                elif c != self._end:
                    self.extended.append(t)
            elif self.verbose and t == self._hashtag and not self.in_group(i.index - 1):
                self.extended.append(t)
                self.extended.extend(self.comments(i))
            else:
                self.extended.append(t)

        return self._empty.join(self.extended)


# Template expander
class ReplaceTemplateExpander(object):
    """Backrefereces."""

    def __init__(self, match, template):
        """Initialize."""

        if template.binary:
            ctokens = ctok.btokens
        else:
            ctokens = ctok.utokens

        self.template = template
        self._esc_end = ctokens["esc_end"]
        self._end = ctokens["end"]
        self._lc = ctokens["lc"]
        self._lc_span = ctokens["lc_span"]
        self._uc = ctokens["uc"]
        self._uc_span = ctokens["uc_span"]
        self.index = -1
        self.end_found = False
        self.parent_span = []
        self._expand_string(match)

    def span_case(self, i, case):
        """Uppercase or lowercase the next range of characters until end marker is found."""

        attr = "lower" if case == _LOWER else "upper"
        parts = []
        try:
            t = next(i)
            in_boundary = i.in_boundary()
            while t != self._esc_end or in_boundary:
                if in_boundary:
                    parts.append(getattr(t, attr)())
                elif len(t) > 1:
                    c = t[1:]
                    if c == self._uc:
                        self.parent_span.append(case)
                        parts.extend(self.single_case(i, _UPPER))
                        self.parent_span.pop()
                    elif c == self._lc:
                        self.parent_span.append(case)
                        parts.extend(self.single_case(i, _LOWER))
                        self.parent_span.pop()
                    elif c == self._uc_span:
                        self.parent_span.append(case)
                        parts.extend(self.span_case(i, _UPPER))
                        self.parent_span.pop()
                    elif c == self._lc_span:
                        self.parent_span.append(case)
                        parts.extend(self.span_case(i, _LOWER))
                        self.parent_span.pop()
                else:
                    parts.append(getattr(t, attr)())
                if self.end_found:
                    self.end_found = False
                    break
                t = next(i)
                in_boundary = i.in_boundary()
        except StopIteration:
            pass
        return parts

    def single_case(self, i, case):
        """Uppercase or lowercase the next character."""

        attr = "lower" if case == _LOWER else "upper"
        parts = []
        try:
            t = next(i)
            in_boundary = i.in_boundary()
            if in_boundary:
                # Because this is a group the parent hasn't seen it yet,
                # we need to first pass over it with the parent's conversion first
                # then follow up with the single.
                if self.parent_span:
                    t = getattr(t, "lower" if self.parent_span[-1] else "upper")()
                parts.append(getattr(t[0:1], attr)() + t[1:])
            elif len(t) > 1:
                # Escaped char; just append.
                c = t[1:]
                chars = []
                if c == self._uc:
                    chars = self.single_case(i, _UPPER)
                elif c == self._lc:
                    chars = self.single_case(i, _LOWER)
                elif c == self._uc_span:
                    chars = self.span_case(i, _UPPER)
                elif c == self._lc_span:
                    chars = self.span_case(i, _LOWER)
                elif c == self._end:
                    self.end_found = True
                if chars:
                    chars[0] = getattr(chars[0][0:1], attr)() + chars[0][1:]
                    parts.extend(chars)
            else:
                parts.append(getattr(t, attr)())
        except StopIteration:
            pass
        return parts

    def _expand_string(self, match):
        """
        Using the template, expand the string.

        Keep track of the match group boundaries for later.
        """

        self.sep = match.string[:0]
        self.text = []
        self.group_boundaries = []
        # Expand string
        char_index = 0
        for x in range(0, len(self.template.literals)):
            index = x
            l = self.template.literals[x]
            if l is None:
                g_index = self.template.get_group_index(index)
                l = match.group(g_index)
                start = char_index
                char_index += len(l)
                self.group_boundaries.append((start, char_index))
                self.text.append(l)
            else:
                start = char_index
                char_index += len(l)
                self.text.append(l)

    def expand(self):
        """
        Expand with backreferences.

        Walk the expanded template string and process
        the new added backreferences and apply the associated
        action.
        """

        # Handle backreferences
        i = ReplaceTokens(self.sep.join(self.text), self.group_boundaries)
        iter(i)
        result = []
        for t in i:
            in_boundary = i.in_boundary()

            # Backreference has been found
            # This is for the neutral state
            # (currently applying no title cases)

            if in_boundary:
                result.append(t)
            elif len(t) > 1:
                c = t[1:]
                if c == self._lc:
                    result.extend(self.single_case(i, _LOWER))
                elif c == self._lc_span:
                    result.extend(self.span_case(i, _LOWER))
                elif c == self._uc:
                    result.extend(self.single_case(i, _UPPER))
                elif c == self._uc_span:
                    result.extend(self.span_case(i, _UPPER))
                elif c == self._end:
                    # This is here just as a reminder that \E is ignored
                    pass
            else:
                result.append(t)

            # Handle extraneous end
            if self.end_found:
                self.end_found = False

        return self.sep.join(result)


def _apply_replace_backrefs(m, repl=None):
    """Expand with either the ReplaceTemplate or the user function, compile on the fly, or return None."""

    if repl is not None and m is not None:
        if hasattr(repl, '__call__'):
            return repl(m)
        elif isinstance(repl, ReplaceTemplate):
            return ReplaceTemplateExpander(m, repl).expand()
        elif isinstance(repl, (compat.string_type, compat.binary_type)):
            return ReplaceTemplateExpander(m, ReplaceTemplate(m.re, repl)).expand()


def _apply_search_backrefs(pattern, flags=0):
    """Apply the search backrefs to the search pattern."""

    if isinstance(pattern, (compat.string_type, compat.binary_type)):
        re_verbose = bool(VERBOSE & flags)
        re_unicode = None
        if compat.PY3 and bool(ASCII & flags):
            re_unicode = False
        elif bool(UNICODE & flags):
            re_unicode = True
        pattern = SearchTemplate(pattern, re_verbose, re_unicode).apply()

    return pattern


def compile_search(pattern, flags=0):
    """Compile with extended search references."""

    return re.compile(_apply_search_backrefs(pattern, flags), flags)


def compile_replace(pattern, repl):
    """Construct a method that can be used as a replace method for sub, subn, etc."""

    call = None
    if pattern is not None:
        if not hasattr(repl, '__call__') and isinstance(pattern, RE_TYPE):
            repl = ReplaceTemplate(pattern, repl)
        call = functools.partial(_apply_replace_backrefs, repl=repl)
    return call


# Convenience methods like re has, but slower due to overhead on each call.
# It is recommended to use compile_search and compile_replace
def expand(m, repl):
    """Expand the string using the replace pattern or function."""

    return _apply_replace_backrefs(m, repl)


def search(pattern, string, flags=0):
    """Search after applying backrefs."""

    return re.search(_apply_search_backrefs(pattern, flags), string, flags)


def match(pattern, string, flags=0):
    """Match after applying backrefs."""

    return re.match(_apply_search_backrefs(pattern, flags), string, flags)


def split(pattern, string, maxsplit=0, flags=0):
    """Split after applying backrefs."""

    return re.split(_apply_search_backrefs(pattern, flags), string, maxsplit, flags)


def findall(pattern, string, flags=0):
    """Findall after applying backrefs."""

    return re.findall(_apply_search_backrefs(pattern, flags), string, flags)


def finditer(pattern, string, flags=0):
    """Finditer after applying backrefs."""

    return re.finditer(_apply_search_backrefs(pattern, flags), string, flags)


def sub(pattern, repl, string, count=0, flags=0):
    """Sub after applying backrefs."""

    pattern = compile_search(pattern, flags)
    return re.sub(pattern, compile_replace(pattern, repl), string, count, flags)


def subn(pattern, repl, string, count=0, flags=0):
    """Subn after applying backrefs."""

    pattern = compile_search(pattern, flags)
    return re.subn(pattern, compile_replace(pattern, repl), string, count, flags)
