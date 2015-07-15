r"""
Backrefs.

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
import sys
from . import uniprops

# Compatibility
PY3 = (3, 0) <= sys.version_info < (4, 0)

if PY3:
    unichar = chr  # noqa
    string_type = str  # noqa
    binary_type = bytes  # noqa

    def iterstring(string):
        """Iterate through a string."""

        if isinstance(string, binary_type):
            for x in range(0, len(string)):
                yield string[x:x + 1]
        else:
            for c in string:
                yield c

    class Tokens(object):

        """Tokens base for PY3."""

        def iternext(self):
            """Common override method."""

        def __next__(self):
            """PY3 iterator compatible next."""

            return self.iternext()

else:
    unichar = unichr  # noqa
    string_type = basestring  # noqa
    binary_type = str  # noqa

    def iterstring(string):
        """Iterate through a string."""

        for c in string:
            yield c

    class Tokens(object):

        """Tokens base for PY2."""

        def iternext(self):
            """Common override method."""

        def next(self):
            """PY2 iterator compatible next."""

            return self.iternext()

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
escape = re.escape
purge = re.purge

RE_TYPE = type(re.compile('', 0))

# Case upper or lower
_UPPER = 0
_LOWER = 1

# Mapping of friendly unicode category names to shorthand codes.
unicode_property_map = {
    # General
    "Control": "Cc",
    "Format": "Cf",
    "Surrogate": "Cs",
    "Private_Use": "Co",
    "Unassigned": "Cn",

    # Letters
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

# Reference indexes
# Keep a list of unicode references and binary and index into them so
# we don't have to translate the strings or waste time searching in a dict.
_DEF_BACK_REF = 0
_REPLACE_TOKENS = 1
_SEARCH_TOKENS = 2  # Not Used
_VERBOSE_TOKENS = 3
_EMPTY = 4
_LS_BRACKET = 5
_RS_BRACKET = 6
_B_SLASH = 7
_ESC_END = 8
_END = 9
_QUOTE = 10
_LC = 11
_LC_SPAN = 12
_UC = 13
_UC_SPAN = 14
_HASHTAG = 15
_NL = 16
_UNI_PROP = 17
_INVERSE_UNI_PROP = 18
_ASCII_LOW_PROPS = 19
_ASCII_UPPER_PROPS = 20
_NEGATIVE_LOWER = 21
_NEGATIVE_UPPER = 22
_NEGATE = 23
_VERBOSE_FLAG = 24
_RE_SEARCH_REF = 25
_RE_SEARCH_REF_VERBOSE = 26
_RE_REPLACE_REF = 27
_RE_IS_VERBOSE = 28
_RE_FLAGS = 29
_LR_BRACKET = 30
_UNICODE_FLAG = 31

# Unicode string related references
utokens = (
    set("abfnrtvAbBdDsSwWZuxg"),     # _DEF_BACK_REF
    set("cCElL"),                    # _REPLACE_TOKENS
    set("cCElLQ"),                   # _SEARCH_TOKENS
    set("# "),                       # _VERBOSE_TOKENS
    "",                              # _EMPTY
    "[",                             # _LS_BRACKET
    "]",                             # _RS_BRACKET
    "\\",                            # _B_SLASH
    "\\E",                           # _ESC_END
    "E",                             # _END
    "Q",                             # _QUOTE
    "l",                             # _LC
    "L",                             # _LC_SPAN
    "c",                             # _UC
    "C",                             # _UC_SPAN
    '#',                             # _HASHTAG
    '\n',                            # _NL
    "p",                             # _UNI_PROP
    "P",                             # _INVERSE_UNI_PROP
    'a-z',                           # _ASCII_LOW_PROPS
    'A-Z',                           # _ASCII_UPPER_PROPS
    '\u0000-\u0060\u007b-\u007f',    # _NEGATIVE_LOWER
    '\u0000-\u0040\u005b-\u007f',    # _NEGATIVE_UPPER
    '^',                             # _NEGATE
    'x',                             # _VERBOSE_FLAG
    re.compile(                      # _RE_SEARCH_REF
        r'''(?x)
        (\\)+
        (
            [(lLcCEQ] |
            %(uni_prop)s
        )? |
        (
            [(lLcCEQ] |
            %(uni_prop)s
        )
        ''' % {"uni_prop": _UPROP}
    ),
    re.compile(                       # _RE_SEARCH_REF_VERBOSE
        r'''(?x)
        (\\)+
        (
            [(lLcCEQ#] |
            %(uni_prop)s
        )? |
        (
            [(lLcCEQ#] |
            %(uni_prop)s
        )
        ''' % {"uni_prop": _UPROP}
    ),
    re.compile(                       # _RE_REPLACE_REF
        r'''(?x)
        (\\)+
        (
            [cClLE]
        )? |
        (
            [cClLE]
        )
        '''
    ),
    re.compile(                       # _RE_IS_VERBOSE
        r'\s*\(\?([iLmsux]+)\)'
    ),
    re.compile(                       # _RE_FLAGS
        r'\(\?([iLmsux]+)\)'
    ),
    '(',                              # _LR_BRACKET
    'u'                               # _UNICODE_FLAG
)

# Byte string related references
btokens = (
    set(                             # _DEF_BACK_REF
        [
            b"a", b"b", b"f", b"n", b"r",
            b"t", b"v", b"A", b"b", b"B",
            b"d", b"D", b"s", b"S", b"w",
            b"W", b"Z", b"u", b"x", b"g"
        ]
    ),
    set(                              # _REPLACE_TOKENS
        [b"c", b"C", b"E", b"l", b"L"]
    ),
    set(                              # _SEARCH_TOKENS
        [b"c", b"C", b"E", b"l", b"L", b"Q"]
    ),
    set([b"#", b" "]),                # _VERBOSE_TOKENS
    b"",                              # _EMPTY
    b"[",                             # _LS_BRACKET
    b"]",                             # _RS_BRACKET
    b"\\",                            # _B_SLASH
    b"\\E",                           # _ESC_END
    b"E",                             # _END
    b"Q",                             # _QUOTE
    b"l",                             # _LC
    b"L",                             # _LC_SPAN
    b"c",                             # _UC
    b"C",                             # _UC_SPAN
    b'#',                             # _HASHTAG
    b'\n',                            # _NL
    b"p",                             # _UNI_PROP
    b"P",                             # _INVERSE_UNI_PROP
    b'a-z',                           # _ASCII_LOW_PROPS
    b'A-Z',                           # _ASCII_UPPER_PROPS
    b'\x00-\x60\x7b-\x7f',            # _NEGATIVE_LOWER
    b'\x00-\x40\x5b-\x7f',            # _NEGATIVE_UPPER
    b'^',                             # _NEGATE
    b'x',                             # _VERBOSE_FLAG
    re.compile(                       # _RE_SEARCH_REF
        br'''(?x)
        (\\)+
        (
            [(lLcCEQ]
        )? |
        (
            [(lLcCEQ]
        )
        '''
    ),
    re.compile(                       # _RE_SEARCH_REF_VERBOSE
        br'''(?x)
        (\\)+
        (
            [(lLcCEQ#]
        )? |
        (
            [(lLcCEQ#]
        )
        '''
    ),
    re.compile(                       # _RE_REPLACE_REF
        br'''(?x)
        (\\)+
        (
            [cClLE]
        )? |
        (
            [cClLE]
        )
        '''
    ),
    re.compile(                       # _RE_IS_VERBOSE
        br'\s*\(\?([iLmsux]+)\)'
    ),
    re.compile(                       # _RE_FLAGS
        br'\(\?([iLmsux]+)\)'
    ),
    b'(',                              # _LR_BRACKET
    b'u'                               # _UNICODE_FLAG
)


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
class ReplaceTokens(Tokens):

    """Tokens."""

    def __init__(self, string, boundaries):
        """Initialize."""

        if isinstance(string, binary_type):
            tokens = btokens
        else:
            tokens = utokens

        self.string = string
        self._b_slash = tokens[_B_SLASH]
        self._re_replace_ref = tokens[_RE_REPLACE_REF]
        self.max_index = len(string) - 1
        self.index = 0
        self.last = 0
        self.current = None
        self.boundaries = boundaries
        self.boundary = self.boundaries.pop(0) if boundaries else (self.max_index + 1, self.max_index + 1)

    def _in_boundary(self, index):
        """Check if index is in current boundary."""

        return self.boundary is not None and index >= self.boundary[0] and index < self.boundary[1]

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


class SearchTokens(Tokens):

    """Tokens."""

    def __init__(self, string, verbose):
        """Initialize."""

        if isinstance(string, binary_type):
            tokens = btokens
        else:
            tokens = utokens

        self.string = string
        if verbose:
            self._re_search_ref = tokens[_RE_SEARCH_REF_VERBOSE]
        else:
            self._re_search_ref = tokens[_RE_SEARCH_REF]
        self._re_flags = tokens[_RE_FLAGS]
        self._lr_bracket = tokens[_LR_BRACKET]
        self._b_slash = tokens[_B_SLASH]
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
                    if m.group(2):
                        self.index += 1
                    else:
                        char += self._b_slash
                else:
                    char += m.group(3)
        elif char == self._lr_bracket:
            m = self._re_flags.match(self.string[self.index:])
            if m:
                char = m.group(0)

        self.index += len(char)
        self.current = char
        return self.current


# Templates
class ReplaceTemplate(object):

    """Replace template."""

    def __init__(self, pattern, template):
        """Initialize."""

        if isinstance(template, binary_type):
            self.binary = True
            tokens = btokens
        else:
            self.binary = False
            tokens = utokens
        self._original = template
        self._back_ref = set()
        self._b_slash = tokens[_B_SLASH]
        self._def_back_ref = tokens[_DEF_BACK_REF]
        self._empty = tokens[_EMPTY]
        self._add_back_references(tokens[_REPLACE_TOKENS])
        self._template = self.__escape_template(template)
        self.groups, self.literals = sre_parse.parse_template(self._template, pattern)

    def get_base_template(self):
        """Return the unmodified template before expansion."""

        return self._original

    def __escape_template(self, template):
        """
        Escape backreferences.

        Because the new backreferences are recognized by python
        we need to escape them so they come out okay.
        """

        new_template = []
        slash_count = 0
        for c in iterstring(template):
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
            if isinstance(arg, binary_type if self.binary else string_type) and len(arg) == 1:
                if arg not in self._def_back_ref and arg not in self._back_ref:
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

    def __init__(self, search, re_verbose=False, re_unicode=False):
        """Initialize."""

        if isinstance(search, binary_type):
            self.binary = True
            tokens = btokens
        else:
            self.binary = False
            tokens = utokens

        self._re_is_verbose = tokens[_RE_IS_VERBOSE]
        self._verbose_flag = tokens[_VERBOSE_FLAG]
        self.verbose = self.is_verbose(search, re_verbose)
        self.unicode = re_unicode
        self._empty = tokens[_EMPTY]
        self._b_slash = tokens[_B_SLASH]
        self._ls_bracket = tokens[_LS_BRACKET]
        self._rs_bracket = tokens[_RS_BRACKET]
        self._lr_bracket = tokens[_LR_BRACKET]
        self._unicode_flag = tokens[_UNICODE_FLAG]
        self._esc_end = tokens[_ESC_END]
        self._end = tokens[_END]
        self._uni_prop = tokens[_UNI_PROP]
        self._inverse_uni_prop = tokens[_INVERSE_UNI_PROP]
        self._ascii_low_props = tokens[_ASCII_LOW_PROPS]
        self._ascii_upper_props = tokens[_ASCII_UPPER_PROPS]
        self._lc = tokens[_LC]
        self._lc_span = tokens[_LC_SPAN]
        self._uc = tokens[_UC]
        self._uc_span = tokens[_UC_SPAN]
        self._quote = tokens[_QUOTE]
        self._negate = tokens[_NEGATE]
        self._negative_upper = tokens[_NEGATIVE_UPPER]
        self._negative_lower = tokens[_NEGATIVE_LOWER]
        self._nl = tokens[_NL]
        self._hashtag = tokens[_HASHTAG]
        if self.verbose:
            self._verbose_tokens = tokens[_VERBOSE_TOKENS]
        else:
            self._verbose_tokens = tuple()
        self.search = search
        self.extended = []
        self.escaped = False
        self.groups = []

    def is_verbose(self, string, verbose):
        """Check if regex pattern is verbose."""

        v = verbose
        if not v:
            m = self._re_is_verbose.match(string.lstrip())
            if m and self._verbose_flag in m.group(1):
                v = True
        return v

    def find_char_groups(self, s):
        """Find character groups."""

        pos = 0
        groups = []
        escaped = False
        found = False
        first = None
        for c in iterstring(s):
            if c == self._b_slash:
                escaped = not escaped
            elif escaped:
                escaped = False
            elif c == self._ls_bracket and not found:
                found = True
                first = pos
            elif c == self._negate and found and (pos == first + 1):
                first = pos
            elif c == self._rs_bracket and found and (pos != first + 1):
                groups.append((first, pos))
                found = False
            pos += 1
        return groups

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

        self.groups = self.find_char_groups(self.search)

        i = SearchTokens(self.search, self.verbose)
        iter(i)

        for t in i:
            if len(t) > 1:
                # handle our stuff

                c = t[1:]

                if t.startswith(self._lr_bracket):
                    if not self.binary and not self.in_group(i.index - 1) and self._unicode_flag in t:
                        self.unicode = True
                    self.extended.append(t)
                elif c.startswith(self._uni_prop):
                    self.extended.extend(self.unicode_props(c[2:-1], self.in_group(i.index - 1)))
                elif c.startswith(self._inverse_uni_prop):
                    self.extended.extend(self.unicode_props(c[2:-1], self.in_group(i.index - 1), negate=True))
                elif c == self._lc:
                    # Postpone evaluation of ASCII props as we don't yet know if unicode flag is enabled
                    self.extended.append(
                        lambda case=_LOWER, in_group=self.in_group(i.index - 1):
                            self.ascii_props(case, in_group)
                    )
                elif c == self._lc_span:
                    # Postpone evaluation of ASCII props as we don't yet know if unicode flag is enabled
                    self.extended.append(
                        lambda case=_LOWER, in_group=self.in_group(i.index - 1), negate=True:
                            self.ascii_props(case, in_group, negate=negate)
                    )
                elif c == self._uc:
                    # Postpone evaluation of ASCII props as we don't yet know if unicode flag is enabled
                    self.extended.append(
                        lambda case=_UPPER, in_group=self.in_group(i.index - 1):
                            self.ascii_props(case, in_group)
                    )
                elif c == self._uc_span:
                    # Postpone evaluation of ASCII props as we don't yet know if unicode flag is enabled
                    self.extended.append(
                        lambda case=_UPPER, in_group=self.in_group(i.index - 1), negate=True:
                            self.ascii_props(case, in_group, negate=negate)
                    )
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

        # Handle ASCII properties now that we know if the unicode flag is set
        count = 0
        for entry in self.extended:
            if not isinstance(entry, (string_type, binary_type)):
                new_entry = entry()
                self.extended[count] = new_entry[0] if new_entry else self._empty
            count += 1

        return self._empty.join(self.extended)


# Template expander
class ReplaceTemplateExpander(object):

    """Backrefereces."""

    def __init__(self, match, template):
        """Initialize."""

        if template.binary:
            tokens = btokens
        else:
            tokens = utokens

        self.template = template
        self._esc_end = tokens[_ESC_END]
        self._end = tokens[_END]
        self._lc = tokens[_LC]
        self._lc_span = tokens[_LC_SPAN]
        self._uc = tokens[_UC]
        self._uc_span = tokens[_UC_SPAN]
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

    if repl is not None:
        if hasattr(repl, '__call__'):
            return repl(m)
        elif isinstance(repl, ReplaceTemplate):
            return ReplaceTemplateExpander(m, repl).expand()
        elif isinstance(repl, (string_type, binary_type)):
            return ReplaceTemplateExpander(m, ReplaceTemplate(m.re, repl)).expand()


def _apply_search_backrefs(pattern, flags=0):
    """Apply the search backrefs to the search pattern."""

    if isinstance(pattern, (string_type, binary_type)):
        re_verbose = VERBOSE & flags
        re_unicode = UNICODE & flags
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
