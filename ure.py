"""
ure - unicode re

A simple script that wraps the re interface with methods to handle unicode properties.
Patterns will all have re.UNICODE enabled and unicode property formats will be replaced
with the unicode characters in that category.

Example:
r"\p{Ll}\p{Lu}"

Licensed under MIT
Copyright (c) 2013 Isaac Muse <isaacmuse@gmail.com>
"""
import re
import sys
try:
    import unicodedata
except:
    from os.path import dirname
    sys.path.append(dirname(sys.executable))
    import unicodedata

PY3 = sys.version_info[0] >= 3
uchr = chr if PY3 else unichr

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

_unicode_properties = None
_unicode_key_pattern = None
_loaded = False


def _build_unicode_property_table(unicode_range):
    """
    Build property table for unicode range.
    """
    table = {}
    p = None
    for i in range(*unicode_range):
        try:
            c = uchr(i)
            p = unicodedata.category(c)
        except:
            continue
        if p[0] not in table:
            table[p[0]] = {}
        if p[1] not in table[p[0]]:
            table[p[0]][p[1]] = []
        table[p[0]][p[1]].append(c)

    # Join as one string
    for k1, v1 in table.items():
        for k2, v2 in v1.items():
            v1[k2] = ''.join(v2)

    return table


def _build_unicode_key_pattern():
    """
    Build regex key pattern
    """
    unicode_prop = r"\p\{(%s)\}"
    unicode_keys = []
    for k1, v1 in _unicode_properties.items():
        unicode_keys.append("%s(?:%s)" % (k1, "|".join(v1.keys())))
    return re.compile(unicode_prop % "|".join(unicode_keys), re.UNICODE)


def _init_unicode():
    """
    Prepare unicode property tables and key pattern
    """
    global _loaded
    global _unicode_properties
    global _unicode_key_pattern
    _unicode_properties = _build_unicode_property_table((0x0000, 0x10FFFF))
    _unicode_key_pattern = _build_unicode_key_pattern()
    _loaded = True


def find_char_groups(s):
    """
    Find character groups
    """
    pos = 0
    groups = []
    escaped = False
    found = False
    first = None
    for c in s:
        if c == "\\":
            escaped = not escaped
        elif escaped:
            escaped = False
        elif c == "[" and not found:
            found = True
            first = pos
        elif c == "]" and found:
            groups.append((first, pos))
        pos += 1
    return groups


def get_unicode_category(prop):
    """
    Retrieve the unicode category from the table
    """
    p1, p2 = (prop[0], prop[1]) if len(prop) > 1 else (prop[0], None)
    return ''.join([x for x in _unicode_properties[p1].values()]) if p2 is None else _unicode_properties[p1][p2]


def parse_unicode_properties(re_pattern):
    """
    Replaces regex property notation with unicode values
    """

    # Init unicode table if it has not already been initialized
    global _loaded
    if not _loaded:
        _init_unicode()

    char_groups = find_char_groups(re_pattern)
    ure_pattern = re_pattern
    for p in reversed(list(_unicode_key_pattern.finditer(re_pattern))):
        v = get_unicode_category(p.group(1))
        brackets = True
        if v is None:
            continue
        for g in char_groups:
            if p.start(0) >= g[0] and p.end(0) <= g[1]:
                brackets = False
                break
        if brackets:
            v = "[" + v + "]"
        ure_pattern = ure_pattern[:p.start(0) - 1] + v + ure_pattern[p.end(0): len(ure_pattern)]
    return ure_pattern


def compile(pattern, flags=0):
    """
    compile after parsing unicode properties and set flag to unicode
    """
    return re.compile(parse_unicode_properties(pattern), flags | re.UNICODE)


def search(pattern, string, flags=0):
    """
    search after parsing unicode properties and set flag to unicode
    """
    re.search(parse_unicode_properties(pattern), string, flags | re.UNICODE)


def match(pattern, string, flags=0):
    """
    match after parsing unicode properties and set flag to unicode
    """
    re.match(parse_unicode_properties(pattern), string, flags | re.UNICODE)


def split(pattern, string, maxsplit=0, flags=0):
    """
    split after parsing unicode properties and set flag to unicode
    """
    re.split(parse_unicode_properties(pattern), string, maxsplit, flags | re.UNICODE)


def findall(pattern, string, flags=0):
    """
    findall after parsing unicode properties and set flag to unicode
    """
    re.findall(parse_unicode_properties(pattern), string, flags | re.UNICODE)


def finditer(pattern, string, flags=0):
    """
    finditer after parsing unicode properties and set flag to unicode
    """
    re.finditer(parse_unicode_properties(pattern), string, flags | re.UNICODE)


def sub(pattern, repl, string, count=0, flags=0):
    """
    sub after parsing unicode properties and set flag to unicode
    """
    re.sub(parse_unicode_properties(pattern), repl, string, count, flags | re.UNICODE)


def subn(pattern, repl, string, count=0, flags=0):
    """
    subn after parsing unicode properties and set flag to unicode
    """
    re.subn(parse_unicode_properties(pattern), repl, string, flags | re.UNICODE)


# _init_unicode()


if __name__ == "__main__":
    print("Testing ure's unicode properties replacement")
    print(parse_unicode_properties(r"[\p{Ll}\p{Lu}]"))
    print(parse_unicode_properties(r"\p{Ll}\p{Lu}"))
