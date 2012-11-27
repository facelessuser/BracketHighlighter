# Version 1.9.0
- Add experimental CFML support (defaulted off)
- Add auto-detection of self-closing tags (defaulted on)

# Version 1.8.0
- Add new commands: "Show Bracket String Escape Mode" and "Toggle Bracket String Escape Mode".  Default is "regex"

# Version 1.7.2
- Feed general bracket type to bracket plugins
- Adjust bracket select plugin to better handle HTML tags

# Version 1.7.1
- Reorganize some settings
- Limit auto-highlight selections by configurable threshold setting

# Version 1.7.0
- Hide parent quote highlighting when child quotes are highlighted
- Allow the searching for brackets in non-quoted code scoped as strings (like regex)
- Add setting "highlight_string_brackets_only" which allows never highlighting quotes but leaves internal string bracket highlighting on
- deprecate "enable_forward_slash_regex_strings" in favor of "find_brackets_in any_strings"

# Version 1.6.2
- Fix adjacent_only with multi_select

# Version 1.6.1
- Suppress string highlighting when adjacent_only is set, but allow internal string brackets to still get highlighted with adjacent_only settings if match_string_brackets is true

# Version 1.6.0
- Add setting to match only when cursor is between brackets

# Version 1.5.3
- Allow turning off gutter icons for multi-select via settings
- Fix multi-select detection
- Default the internal settings if setting is not found

# Version 1.5.2
- Use tiny icons when line height is less than 16
- Use no icon if icon cannot be found
- Optimize png icons

# Version 1.5.1
- Ignore selection/edit events inside the main routine

# Version 1.5.0
- More responsive highlighting (thanks tito); delay setting no longer needed
- Organize bracket plugins
- Included more configurable custom gutter icons

# Version 1.4.1
- Make adjusment to regex modifier code to correctly count back modifiers in perl

# Version 1.4.0
- Account for perl regex, substitutions, and translations surrounded by "/" for string bracket matching
- Account for regex modifiers when matching regex surrounded by "/" in javascript and perl

# Version 1.3.0
- Fixed escaped brackets in string handling.  Also a bit more efficient.

# Version 1.2.0
- Fix angle bracket avoidance when finding brackets inside strings, and make it cleaner

# Version 1.1.0
- Add python raw string support for quote highlighting
- Add highlighting of brackets in strings; will work in all strings, but mainly meant for regex.  True by default
- Add support for targetting regex strings like in javascript that are scoped as strings, but are not quoted, but use '/'s. True by default

# Version 1.0.0
- All previous work and releases
