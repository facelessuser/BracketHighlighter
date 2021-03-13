# About BracketHighlighter

## Overview

BracketHighlighter matches a variety of brackets such as: `[]`, `()`, `{}`, `""`, `''`, `#!xml <tag></tag>`, and even
custom brackets.

This was originally forked from pyparadigm's _SublimeBrackets_ and _SublimeTagmatcher_ (both are no longer available). I
forked his repositories to fix a number issues I add some features I had wanted.  I also wanted to improve the
efficiency of the matching. Moving forward, I have thrown away all of the code and have completely rewritten the entire
code base to allow for more flexibility, faster matching, and a more feature rich experience.

![screenshot](images/Example1.png)

## Feature List

- Customizable to highlight almost any bracket.
- Customizable bracket highlight style.
- High visibility bracket highlight mode.
- Selectively disable or enable specific matching of tags, brackets, or quotes.
- Selectively use an allowlist or blocklist for matching specific tags, brackets, or quotes based on language.
- When bound to a shortcut, allow options to show line count and char count between match in the status bar.
- Highlight basic brackets within strings.
- Works with multi-select.
- Configurable custom gutter icons.
- Toggle bracket escape mode for string brackets (regex|string).
- Bracket plugins that can jump between bracket ends, select content, etc.

## Credits

- pyparadigm: for his original efforts with SublimeBrackets and SublimeTagmatcher which originally BracketHighlighter
  was built off of and the inspiration for this project.
- BoundInCode: for his Tag icon.

--8<-- "refs.md"
