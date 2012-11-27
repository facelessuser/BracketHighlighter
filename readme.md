# About
This is a fork of pyparadigm's _SublimeBrackets_ and _SublimeTagmatcher_ (both are no longer available).  I forked this to fix some issues I had and to add some features I wanted.  I also wanted to improve the efficiency of the matching.  This cuts down on the parallel searching that is now streamlined in one search.  Since then, many new features have been added as well.

<img src="http://dl.dropbox.com/u/342698/BracketHighlighter/Example1.png" border="0">

## Overview
Bracket Highlighter matches a variety of brackets such as: ```[]```, ```()```, ```{}```, ```""```, ```''```, ```<tag></tag>```, and even custom brackets.

# FeatureList
- Customizable to highlight almost any bracket
- Customizable bracket highlight style
- High visibility bracket highlight mode
- Selectively disable or enable specific matching of tags, brackets, or quotes
- Selectively whitelist or blacklist matching of specific tags, brackets, or quotes based on language
- When bound to a shortcut, allow option to show line count and char count between match in the status bar
- Highlight basic brackets within strings
- Works with multi-select
- Configurable custom gutter icons
- Toggle bracket escape mode for string brackets (regex|string)
- Bracket plugins that can jump between bracket ends, select content, remove brackets and/or content, wrap selectios with brackets, swap brackets, swap quotes (handling quote escaping between the main quotes), fold/unfold conent between brackets, toggle through tag attribute selecection, select both the opening and closing tag name to change both simultaneously.

# General Use
Todo

# Configuring Shortcuts
No shortcuts are provided by default so as not to conflict with other plugins or with default Sublime Text shortcuts, but an example shortcut file has been provided that can be adapted to fit a user's need.

# Configuring Brackets
Todo

# Configuring Highlight Style
Todo

# Built-in Bracket Plugins
Todo

# Bracket Plugin API
Todo

# Credits
- pyparadigm: for his original efforrts with SublimeBrackets and SublimeTagmatcher which originally BracketHighlighter was built off of and the inspiration behind the current implementation.
- BoundInCode: for his Tag icon

# Version 2.0.0
- Re-write of BracketHighlighter

# Version Older
- See [Complete Changelog](https://github.com/facelessuser/BracketHighlighter/blob/BH2/CHANGELOG.md)
