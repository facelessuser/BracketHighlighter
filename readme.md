# About
This is a fork of pyparadigm's SublimeBrackets and SublimeTagmatcher (both are no longer available).  I forked this to fix some issues I had and to add some features I wanted.  I also wanted to improve the efficiency of the matching.  This cuts down on the parallel searching that is now streamlined in one search.  Since then, many new features have been added as well.

![Options Screenshot](https://github.com/facelessuser/BracketHighlighter/raw/master/example.png)

# Installation 
- Download is available in Package Control or you can [download](https://github.com/facelessuser/BracketHighlighter/zipball/master "download") or clone directly and drop into your Sublime Text 2 packages directory (plugin folder must be named BracketHighlighter)
- You may need to restart Sublime Text 2 after installation

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
- Bracket related plugins

# Included Plugins
- bracketselect: move cursor to opening bracket or closing bracket or select all content between brackets
- foldbracket: fold according to brackets
- swapbrackets: change the current selected brackets to another bracket type
- swapquotes: change the currently selected quotes from single to double or double to single (scope based)
- tagattrselect: cycle through selecting html tags
- tagnameselect: select the name in the opening and closing tag

# Options
- Open BracketHighlighter.sublime-settings and configure your preferences (can be accessed from menu).
- Change the scope, highlight style, icon for bracket types, which brackets to match, set search thresholds, etc.
- Save the file and your options should take effect immediately.

#Changing Colors
The color is based on the scope you assign to the highlight. The color of the scope is defined by your theme file.  By default, the scope is "entity.name.class", but you could change it to "keyword" or any other scope in your theme.

    //Scope? (Defined in theme files.) ->
    //Examples: (keyword/string/number)
    "quote_scope" : "entity.name.class",
    "curly_scope" : "entity.name.class",
    "round_scope" : "entity.name.class",
    "square_scope": "entity.name.class",
    "angle_scope" : "entity.name.class",
    "tag_scope"   : "entity.name.class",

If you want more control of the colors, you can define your own scopes.

    <dict>
        <key>name</key>
        <string>Bracket Tag</string>
        <key>scope</key>
        <string>bracket.tag</string>
        <key>settings</key>
        <dict>
            <key>foreground</key>
            <string>#FD971F</string>
        </dict>
    </dict>
    <dict>
        <key>name</key>
        <string>Bracket Curly</string>
        <key>scope</key>
        <string>bracket.curly</string>
        <key>settings</key>
        <dict>
            <key>foreground</key>
            <string>#66D9EF</string>
        </dict>
    </dict>
    <dict>
        <key>name</key>
        <string>Bracket Round</string>
        <key>scope</key>
        <string>bracket.round</string>
        <key>settings</key>
        <dict>
            <key>foreground</key>
            <string>#F92672</string>
        </dict>
    </dict>
    <dict>
        <key>name</key>
        <string>Bracket Square</string>
        <key>scope</key>
        <string>bracket.square</string>
        <key>settings</key>
        <dict>
            <key>foreground</key>
            <string>#A6E22E</string>
        </dict>
    </dict>
    <dict>
        <key>name</key>
        <string>Bracket Angle</string>
        <key>scope</key>
        <string>bracket.angle</string>
        <key>settings</key>
        <dict>
            <key>foreground</key>
            <string>#AE81FF</string>
        </dict>
    </dict>
    <dict>
        <key>name</key>
        <string>Bracket Quote</string>
        <key>scope</key>
        <string>bracket.quote</string>
        <key>settings</key>
        <dict>
            <key>foreground</key>
            <string>#FAF60A</string>
        </dict>
    </dict>
    
# Version 1.3
- Fixed escaped brackets in string handling.  Also a bit more efficient.

# Version 1.2
- Fix angle bracket avoidance when finding brackets inside strings, and make it cleaner

# Version 1.1
- Add python raw string support for quote highlighting
- Add highlighting of brackets in strings; will work in all strings, but mainly meant for regex.  True by default
- Add support for targetting regex strings like in javascript that are scoped as strings, but are not quoted, but use '/'s. True by default

# Version 1.0
- All previous work and releases
