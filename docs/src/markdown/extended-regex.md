# Extended Regex Guide

## Overview

BH uses Python's Re regular expression engine, but it also adds some additional back references to aid in the creation
of bracket patterns.  This is done with a custom wrapper called Backrefs that was originally written for
[RegReplace][regreplace].

Backrefs was written to add various additional back references that are known to some regex engines, but not to Python's
Re.  Backrefs adds: `\p`, `\P`, `\u`, `\U`, `\l`, `\L`, `\Q` or `\E` (though `\u` and `\U` are replaced with `\c` and
`\C`).

You can read more about Backrefs' features in [Backrefs' documentation][backrefs].

## Getting the Latest Backrefs

It is not always clear when Package Control updates dependencies.  So to force dependency updates, you can run Package
Control's `Satisfy Dependencies` command which will update to the latest release.

## Using Backrefs in BracketHighlighter Plugins

You can import Backrefs into a `bh_plugin`:

```python
from backrefs as bre
```

Backrefs does provide a wrapper for all of Re's normal functions such as `match`, `sub`, etc., but it is recommended to
pre-compile your search patterns **and** your replace patterns for the best performance; especially if you plan on
reusing the same pattern multiple times.  As Re does cache a certain amount of the non-compiled calls, you will be
spared from some of the performance hit, but Backrefs does not cache the pre-processing of search and replace patterns.

To use pre-compiled functions, you compile the search pattern with `compile_search`.  If you want to take advantage of
replace Backrefs, you need to compile the replace pattern as well.  Notice the compiled pattern is fed into the replace
pattern; you can feed the replace compiler the string representation of the search pattern as well, but the compiled
pattern will be faster and is the recommended way.

```py
pattern = bre.compile_search(r'somepattern', flags)
replace = bre.compile_replace(pattern, r'\1 some replace pattern')
```

Then you can use the complied search pattern and replace

```py
text = pattern.sub(replace, r'sometext')
```

or

```py
m = pattern.match(r'sometext')
if m:
    text = replace(m)  # similar to m.expand(template)
```

To use the non-compiled search/replace functions, you call them just them as you would in Re; the names are the same.
Methods like `sub` and `subn` will compile the replace pattern on the fly if given a string.

```python
for m in bre.finditer(r'somepattern', 'some text', bre.UNICODE | bre.DOTALL):
    # do something
```

If you want to replace without compiling, you can use the `expand` method.

```python
m = bre.match(r'sometext')
if m:
    text = bre.expand(m, r'replace pattern')
```

--8<-- "refs.md"
