# BracketHighlighter
Bracket Highlighter matches a variety of brackets such as: `[]`, `()`, `{}`, `""`, `''`, `<tag></tag>`, and even custom brackets.

This is a fork of pyparadigm's _SublimeBrackets_ and _SublimeTagmatcher_ (both are no longer available).  I forked this to fix some issues I had and to add some features I had wanted.  I also wanted to improve the efficiency of the matching.  This cuts down on the parallel searching that is now streamlined in one search.  Since then, I have rewritten the entire code base to bring more flexibility, speed, and features.

<img src="http://dl.dropbox.com/u/342698/BracketHighlighter/Example1.png" border="0">

# Feature List
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
- Bracket plugins that can jump between bracket ends, select content, remove brackets and/or content, wrap selections with brackets, swap brackets, swap quotes (handling quote escaping between the main quotes), fold/unfold content between brackets, toggle through tag attribute selection, select both the opening and closing tag name to change both simultaneously.

# Installation
The recommended installation method is via Package Control.  Learn more here: https://sublime.wbond.net/.

## Sublime Text 3 Support?
ST3 support is found here: https://github.com/facelessuser/BracketHighlighter/tree/ST3.  All current development is being done on ST3.

## Sublime Text 2 Support?
ST2 support is found here: https://github.com/facelessuser/BracketHighlighter/tree/ST2, but development has been halted on ST2

# Issues
When filing issues, please state the OS and sublime version along with a detailed description of the problem including how to reproduce the issue.  Only ST3 issues will be addressed.

# Pull Requests
Pull requests must be done against the main branch.  When I am ready, the main branch will be merged into the relevant supported branch.  For ST2 only rule defintions will be accepted for pull requests. But ST2 pull requests must be done against the ST2 branch and the relevant matching changes must be made to the main as well to keep the rules up to date on both branches.  ST2 pull requests will only be accepted if the main branch and the ST2 branch are pulled in order to save me work.  I will not back port rules ST2, but I will allow the community to do so.

# Credits
- pyparadigm: for his original efforts with SublimeBrackets and SublimeTagmatcher which originally BracketHighlighter was built off of and the inspiration behind the current implementation.
- BoundInCode: for his Tag icon
