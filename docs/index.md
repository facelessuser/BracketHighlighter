# BracketHighlighter {: .doctitle}
A bracket matcher and highlighter for Sublime.

---

## Overview
Bracket Highlighter matches a variety of brackets such as: `[]`, `()`, `{}`, `""`, `''`, `#!xml <tag></tag>`, and even custom brackets.

This was originally forked from pyparadigm's _SublimeBrackets_ and _SublimeTagmatcher_ (both are no longer available).  I forked this to fix some issues I had and to add some features I had wanted.  I also wanted to improve the efficiency of the matching.

Moving forward, I have thrown away all of the code and have completely rewritten the entire code base to allow for a more flexibility, faster, and more feature rich experience.

![screenshot](images/Example1.png)

## Feature List
- Customizable to highlight almost any bracket.
- Customizable bracket highlight style.
- High visibility bracket highlight mode.
- Selectively disable or enable specific matching of tags, brackets, or quotes.
- Selectively whitelist or blacklist matching of specific tags, brackets, or quotes based on language.
- When bound to a shortcut, allow option to show line count and char count between match in the status bar.
- Highlight basic brackets within strings.
- Works with multi-select.
- Configurable custom gutter icons.
- Toggle bracket escape mode for string brackets (regex|string).
- Bracket plugins that can jump between bracket ends, select content, remove brackets and/or content, wrap selections with brackets, swap brackets, swap quotes (handling quote escaping between the main quotes), fold/unfold content between brackets, toggle through tag attribute selection, select both the opening and closing tag name to change both simultaneously.

## Credits
- pyparadigm: for his original efforts with SublimeBrackets and SublimeTagmatcher which originally BracketHighlighter was built off of and the inspiration for this project.
- BoundInCode: for his Tag icon.

*[BH]: BracketHighlighter
*[ST2]: Sublime Text 2
*[ST3]: Sublime Text 3
