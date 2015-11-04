r"""
Backrefs for the 'regex' module.

Add the ability to use the following backrefs with re:

    * \Q and \Q...\E - Escape/quote chars (search)
    * \c and \C...\E - Uppercase char or chars (replace)
    * \l and \L...\E - Lowercase char or chars (replace)

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
import re
from . import bre
from . import compat
from . import common_tokens as ctok
import functools
try:
    import regex
    REGEX_SUPPORT = True
except Exception:  # pragma: no coverage
    REGEX_SUPPORT = False

if REGEX_SUPPORT:
    # Expose some common re flags and methods to
    # save having to import re and backrefs libs
    D = regex.D
    DEBUG = regex.DEBUG
    A = regex.A
    ASCII = regex.ASCII
    B = regex.B
    BESTMATCH = regex.BESTMATCH
    E = regex.E
    ENHANCEMATCH = regex.ENHANCEMATCH
    F = regex.F
    FULLCASE = regex.FULLCASE
    I = regex.I
    IGNORECASE = regex.IGNORECASE
    L = regex.L
    LOCALE = regex.LOCALE
    M = regex.M
    MULTILINE = regex.MULTILINE
    R = regex.R
    REVERSE = regex.REVERSE
    S = regex.S
    DOTALL = regex.DOTALL
    U = regex.U
    UNICODE = regex.UNICODE
    X = regex.X
    VERBOSE = regex.VERBOSE
    V0 = regex.V0
    VERSION0 = regex.VERSION0
    V1 = regex.V1
    VERSION1 = regex.VERSION1
    W = regex.W
    WORD = regex.WORD
    P = regex.P
    POSIX = regex.POSIX
    DEFAULT_VERSION = regex.DEFAULT_VERSION
    REGEX_TYPE = type(regex.compile('', 0))
    escape = regex.escape
    purge = regex.purge

    utokens = {
        "regex_flags": re.compile(
            r'(?s)(\\.)|\(\?((?:[Laberuxp]|V0|V1|-?[imsfw])+)[):]|(.)'
        ),
        "regex_search_ref": re.compile(
            r'''(?x)
            (\\)+
            (
                [(EQ]
            )? |
            (
                [(EQ]
            )
            '''
        ),
        "regex_search_ref_verbose": re.compile(
            r'''(?x)
            (\\)+
            (
                [(EQ#]
            )? |
            (
                [(EQ#]
            )
            '''
        ),
        "v0": 'V0',
        "v1": 'V1'
    }

    btokens = {
        "regex_flags": re.compile(
            br'(?s)(\\.)|\(\?((?:[Laberuxp]|V0|V1|-?[imsfw])+)[):]|(.)'
        ),
        "regex_search_ref": re.compile(
            br'''(?x)
            (\\)+
            (
                [EQ]
            )? |
            (
                [EQ]
            )
            '''
        ),
        "regex_search_ref_verbose": re.compile(
            br'''(?x)
            (\\)+
            (
                [EQ#]
            )? |
            (
                [EQ#]
            )
            '''
        ),
        "v0": b'V0',
        "v1": b'V1'
    }

    class RegexSearchTokens(compat.Tokens):
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
                self._re_search_ref = tokens["regex_search_ref_verbose"]
            else:
                self._re_search_ref = tokens["regex_search_ref"]
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

            Count escaped Q, E and backslash as a single char.
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

    class RegexSearchTemplate(object):
        """Search Template."""

        def __init__(self, search, re_verbose=False, re_version=0):
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
            self._esc_end = ctokens["esc_end"]
            self._end = ctokens["end"]
            self._quote = ctokens["quote"]
            self._negate = ctokens["negate"]
            self._regex_flags = tokens["regex_flags"]
            self._nl = ctokens["nl"]
            self._hashtag = ctokens["hashtag"]
            self._V0 = tokens["v0"]
            self._V1 = tokens["v1"]
            self.search = search
            if regex.DEFAULT_VERSION == V0:
                self.groups, quotes = self.find_char_groups_v0(search)
            else:  # pragma: no cover
                self.groups, quotes = self.find_char_groups_v1(search)
            self.verbose, self.version = self.find_flags(search, quotes, re_verbose, re_version)
            if self.version != regex.DEFAULT_VERSION:
                if self.version == V0:  # pragma: no cover
                    self.groups = self.find_char_groups_v0(search)[0]
                else:
                    self.groups = self.find_char_groups_v1(search)[0]
            if self.verbose:
                self._verbose_tokens = ctokens["verbose_tokens"]
            else:
                self._verbose_tokens = tuple()
            self.extended = []

        def find_flags(self, s, quotes, re_verbose, re_version):
            """Find verbose and unicode flags."""

            new = []
            start = 0
            verbose_flag = re_verbose
            version_flag = re_version
            avoid = quotes + self.groups
            avoid.sort()
            if version_flag and verbose_flag:
                return bool(verbose_flag), version_flag
            for a in avoid:
                new.append(s[start:a[0] + 1])
                start = a[1]
            new.append(s[start:])
            for m in self._regex_flags.finditer(self._empty.join(new)):
                if m.group(2):
                    if self._verbose_flag in m.group(2):
                        verbose_flag = True
                    if self._V0 in m.group(2):
                        version_flag = V0
                    elif self._V1 in m.group(2):
                        version_flag = V1
                if version_flag and verbose_flag:
                    break
            return bool(verbose_flag), version_flag if version_flag else regex.DEFAULT_VERSION

        def find_char_groups_v0(self, s):
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

        def find_char_groups_v1(self, s):
            """Find character groups."""

            pos = 0
            groups = []
            quotes = []
            quote_found = False
            quote_start = 0
            escaped = False
            found = 0
            first = None
            sub_first = None
            for c in compat.iterstring(s):
                if c == self._b_slash:
                    # Next char is escaped
                    escaped = not escaped
                elif escaped and found == 0 and not quote_found and c == self._quote:
                    quote_found = True
                    quote_start = pos - 1
                    escaped = False
                elif escaped and found == 0 and quote_found and c == self._end:
                    quotes.append((quote_start, pos))
                    quote_found = False
                    escaped = False
                elif escaped:
                    # Escaped handled
                    escaped = False
                elif quote_found:
                    pass
                elif c == self._ls_bracket and not found:
                    # Start of first char set found
                    found += 1
                    first = pos
                elif c == self._ls_bracket and found:
                    # Start of sub char set found
                    found += 1
                    sub_first = pos
                elif c == self._negate and found == 1 and (pos == first + 1):
                    # Found ^ at start of first char set; adjust 1st char pos
                    first = pos
                elif c == self._negate and found > 1 and (pos == sub_first + 1):
                    # Found ^ at start of sub char set; adjust 1st char sub pos
                    sub_first = pos
                elif c == self._rs_bracket and found == 1 and (pos != first + 1):
                    # First char set closed; log range
                    groups.append((first, pos))
                    found = 0
                elif c == self._rs_bracket and found > 1 and (pos != sub_first + 1):
                    # Sub char set closed; decrement depth counter
                    found -= 1
                pos += 1
            if quote_found:
                quotes.append((quote_start, pos - 1))
            return groups, quotes

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

            i = RegexSearchTokens(self.search, self.verbose)
            iter(i)

            for t in i:
                if len(t) > 1:
                    # handle our stuff

                    c = t[1:]

                    if c[0:1] in self._verbose_tokens:
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

    class RegexReplaceTemplate(bre.ReplaceTemplate):
        """Replace template for the regex module."""

        def parse_template(self, pattern):
            """
            Parse template for the regex module.

            Do NOT edit the literal list returned by
            _compile_replacement_helper as you will edit
            the original cached value.  Copy the values
            instead.
            """

            self.groups = []
            self.literals = []
            literals = regex._compile_replacement_helper(pattern, self._template)
            count = 0
            for part in literals:
                if isinstance(part, int):
                    self.literals.append(None)
                    self.groups.append((count, part))
                else:
                    self.literals.append(part)
                count += 1

    def _apply_replace_backrefs(m, repl=None):
        """Expand with either the RegexReplaceTemplate or the user function, compile on the fly, or return None."""

        if repl is not None and m is not None:
            if hasattr(repl, '__call__'):
                return repl(m)
            elif isinstance(repl, RegexReplaceTemplate):
                return bre.ReplaceTemplateExpander(m, repl).expand()
            elif isinstance(repl, (compat.string_type, compat.binary_type)):
                return bre.ReplaceTemplateExpander(m, RegexReplaceTemplate(m.re, repl)).expand()

    def _apply_search_backrefs(pattern, flags=0):
        """Apply the search backrefs to the search pattern."""

        if isinstance(pattern, (compat.string_type, compat.binary_type)):
            re_verbose = VERBOSE & flags
            if flags & V0:
                re_version = V0
            elif flags & V1:
                re_version = V1
            else:
                re_version = 0
            pattern = RegexSearchTemplate(pattern, re_verbose, re_version).apply()

        return pattern

    def compile_search(pattern, flags=0, **kwargs):
        """Compile with extended search references."""

        return regex.compile(_apply_search_backrefs(pattern, flags), flags, **kwargs)

    def compile_replace(pattern, repl):
        """Construct a method that can be used as a replace method for sub, subn, etc."""

        call = None
        if pattern is not None:
            if not hasattr(repl, '__call__') and isinstance(pattern, REGEX_TYPE):
                repl = RegexReplaceTemplate(pattern, repl)
            call = functools.partial(_apply_replace_backrefs, repl=repl)
        return call

    # Convenience methods like re has, but slower due to overhead on each call.
    # It is recommended to use compile_search and compile_replace
    def expand(m, repl):
        """Expand the string using the replace pattern or function."""

        return _apply_replace_backrefs(m, repl)

    def match(pattern, string, flags=0, pos=None, endpos=None, partial=False, concurrent=None, **kwargs):
        """Wrapper for match."""

        return regex.match(
            _apply_search_backrefs(pattern, flags), string,
            flags, pos, endpos, partial, concurrent, **kwargs
        )

    def fullmatch(pattern, string, flags=0, pos=None, endpos=None, partial=False, concurrent=None, **kwargs):
        """Wrapper for fullmatch."""

        return regex.fullmatch(
            _apply_search_backrefs(pattern, flags), string,
            flags, pos, endpos, partial, concurrent, **kwargs
        )

    def search(pattern, string, flags=0, pos=None, endpos=None, partial=False, concurrent=None, **kwargs):
        """Wrapper for search."""

        return regex.search(
            _apply_search_backrefs(pattern, flags), string,
            flags, pos, endpos, partial, concurrent, **kwargs
        )

    def sub(pattern, repl, string, count=0, flags=0, pos=None, endpos=None, concurrent=None, **kwargs):
        """Wrapper for sub."""

        pattern = compile_search(pattern, flags)
        return regex.sub(
            pattern, compile_replace(pattern, repl), string,
            count, flags, pos, endpos, concurrent, **kwargs
        )

    def subf(pattern, format, string, count=0, flags=0, pos=None, endpos=None, concurrent=None, **kwargs):
        """Wrapper for subf."""

        return regex.subf(
            _apply_search_backrefs(pattern, flags), format, string,
            count, flags, pos, endpos, concurrent, **kwargs
        )

    def subn(pattern, repl, string, count=0, flags=0, pos=None, endpos=None, concurrent=None, **kwargs):
        """Wrapper for subn."""

        pattern = compile_search(pattern, flags)
        return regex.subn(
            pattern, compile_replace(pattern, repl), string,
            count, flags, pos, endpos, concurrent, **kwargs
        )

    def subfn(pattern, format, string, count=0, flags=0, pos=None, endpos=None, concurrent=None, **kwargs):
        """Wrapper for subfn."""

        return regex.subfn(
            _apply_search_backrefs(pattern, flags), format, string,
            count, flags, pos, endpos, concurrent, **kwargs
        )

    def split(pattern, string, maxsplit=0, flags=0, concurrent=None, **kwargs):
        """Wrapper for split."""

        return regex.split(
            _apply_search_backrefs(pattern, flags), string,
            maxsplit, flags, concurrent, **kwargs
        )

    def splititer(pattern, string, maxsplit=0, flags=0, concurrent=None, **kwargs):
        """Wrapper for splititer."""

        return regex.splititer(
            _apply_search_backrefs(pattern, flags), string,
            maxsplit, flags, concurrent, **kwargs
        )

    def findall(
        pattern, string, flags=0, pos=None, endpos=None, overlapped=False,
        concurrent=None, **kwargs
    ):
        """Wrapper for findall."""

        return regex.findall(
            _apply_search_backrefs(pattern, flags), string,
            flags, pos, endpos, overlapped, concurrent, **kwargs
        )

    def finditer(
        pattern, string, flags=0, pos=None, endpos=None, overlapped=False,
        partial=False, concurrent=None, **kwargs
    ):
        """Wrapper for finditer."""

        return regex.finditer(
            _apply_search_backrefs(pattern, flags), string,
            flags, pos, endpos, overlapped, partial, concurrent, **kwargs
        )
