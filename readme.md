# About
This is a fork of pyparadigm's [SublimeBrackets](https://github.com/pyparadigm/SublimeBrackets "Go to SublimeBrackets.")
I forked this to fix some issues I had and to add some features I wanted.  I also wanted to improve the efficiency of the matching.
I also merged in pyparadigm's SublimeTagmatcher as well.  This cuts down on the parallel searching that is now streamlined in one search.

# Installation 
* Latest version: [Click here to download.](https://github.com/facelessuser/BracketHighlighter/zipball/master "Click here to download lastest version.")
- Must be running **Sublime Text 2 Build 2108** or higher.
- Drop the folder into your Sublime Text 2 packages directory.
- You may need to restart Sublime Text 2

# Features
- Customizable highlighting of brackets (),[],<>,{}
- Customizable highlighting of Tags (supports unary tags and supports self closing /> (HTML5 coming))
- Customizable highlighting of quotes
- Selectively disable or enable specific matching of tags, brackets, or quotes
- Selectively whitelist or blacklist matching of specific tags, brackets, or quotes based on language
- When using on demand shortcut, show line count and char count between match in the status bar
- Shortcuts for moving cursor to beginning or end of bracketed content (will focus on beginning or end bracket if not currently multi-selecting)
- Shortcut for selecting all of the bracketed content
- Shortcut for chaning quote style (accounts for escaped quotes as well)
- Works with multi-select

# Options
- Open BracketHighlighter.sublime-settings and configure your preferences (can be accessed from menu).
- Change the scope, highlight style, icon for bracket types, which brackets to match, set search thresholds, etc.
- Save the file and your options should take effect immediately.

# Screenshot
![Options Screenshot](https://github.com/facelessuser/BracketHighlighter/raw/master/example.png)
