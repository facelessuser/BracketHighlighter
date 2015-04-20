# General Use
In general, BracketHighlighter (BH) will highlight brackets (or defined bracket like start and end blocks) surrounding the cursor.  By default, BH will put opening and closing icons in the gutter of the corresponding line containing open or closing bracket. BH, by default, will underline the closing and opening bracket as well.

## Built-in Supported brackets
Currently BH supports the following brackets out of the box:

- round
- square
- curly
- angle
- single and double quotes
- python single and double quotes (unicode and raw)
- python triple single and double quotes (unicode and raw)
- Javascript regex
- Perl regex
- Ruby regex
- Markdown italic
- Markdown bold
- CSSedit groups
- Ruby conditional statements
- C/C++ compiler switches
- PHP conditional keywords
- Erlang conditional statements
- HTML/ColdFusion/XML tags
- Bash conditional and looping constructs

BH also supports highlighting basic sub brackets `(), [], {}` within supported regex and strings.

## Additional Features
BH has a couple of additional features built-in.

### Toggle Global Enable (bh_toggle_enable)
This command enables and disables BH globally

### Toggle String Bracket Escape Mode (bh_toggle_string_escape_mode)
This toggles BH's recognition mode of escaped sub brackets in strings and regex.  The modes are string escape mode and regex escape mode.

### Settings
When changing settings, you should copy the entire `bh_core.sublime-settings` to your `User` folder before changing.  Style and color will be discussed in greater depth in the `Configuring Highlight Style` section.

These are the basic settings you can change:
```javascript
    //Debug logging
    "debug_enable": false,

    // When only either the left or right bracket can be found
    // this defines if the unmatched bracket should be shown.
    "show_unmatched" : true,

    // Do the opposite of "show_unmatched" for the languages listed below
    "show_unmatched_exceptions": [],

    // Enable high visibility by default when sublime starts up
    // If sublime is already running and this gets changed,
    // you will not see any changes (restart required to see change)
    "high_visibility_enabled_by_default": false,

    // Experimental: Creates a visible bar at the beginning of all lines between
    // multiline bracket spans.
    "content_highlight_bar": false,

    // Experimental: Align the content highlight bar at the bracket indent level
    "align_content_highlight_bar": false,

    // High visibility style and color for high visibility mode
    // (solid|outline|underline)
    // ST3 has additional options of (thin_underline|squiggly|stippled)
    "high_visibility_style": "outline",

    // (scope|__default__|__bracket__)
    "high_visibility_color": "__bracket__",

    // Match brackets only when the cursor is touching the inside of the bracket
    "match_only_adjacent": false,

    // Character threshold to search
    "search_threshold": 5000,

    // Ignore threshold
    "ignore_threshold": false,

    // Set mode for string escapes to ignore (regex|string)
    "bracket_string_escape_mode": "string",

    // Set max number of multi-select brackets that will be searched automatically
    "auto_selection_threshold" : 10,

    // Enable this to completely kill highlighting if "auto_selection_threshold"
    // is exceeded.  Default is to highlight up to the "auto_selection_threshold".
    "kill_highlight_on_threshold": true,

    // Disable gutter icons when doing multi-select
    "no_multi_select_icons": false,
```

### Bracket Plugins
Bh is also extendable via plugins and provides an number of plugins by default.  See [Bracket Plugins](#bracket-plugins) to learn more about the included plugins.

## Bracket Plugin
BH provides a number of built in Bracket Plugins that take advantage of BH's matching to provide additional features.  Most plugin features are available via the Tools->Packages->BracketHighlighter menu or the command palette.  To see how to configure shortcuts, see the `Example.sublime-settings` file.

### Bracket Select Plugin
This plugin changes the selection inside between the brackets.  It can select the content or move the bracket to the opening and closing bracket.  Behavior is slightly modified for tags.

### Bracket Remove Plugin
Removes the surrounding brackets.

### Fold Bracket Plugin
Folds the content of the current surrounding brackets.

### Swap Quotes Plugin
Swap the quotes style of surrounding quotes from double to single or vice versa.  It also handles escaping and unescaping of sub quotes.

### Tag Plugin
Plugin used to help highlight tags.

Additional tag settings found in `bh_core.sublime-settings`:

```javascript
    /* Plugin settings */

    // Style to use for matched tags
    "tag_style": "tag",

    // Scopes to exclude from tag searches
    "tag_scope_exclude": ["string", "comment"],

    // Determine which style of tag-matching to use in which syntax
    "tag_mode": {
        "xhtml": ["XML"],
        "html": ["HTML", "HTML 5", "PHP"],
        "cfml": ["HTML+CFML", "ColdFusion", "ColdFusionCFC"]
    }
```

### Tag Attribute Select Plugin
Cycle through selecting tag attributes of tags.

### Tag Name Select Plugin
Select the opening and closing tag name of current tag.

### Bracket Wrapping Plugin
Wrap the current selection with supported bracket of your choice.  Wrapping definitions are configured in `bh_wrapping.sublime-settings`.

### Bracket Swapping Plugin
Swap the current surrounding bracket with supported bracket of your choice.  Swapping definitions are configured in `bh_swapping.sublime-settings`.

## Shortcuts
By default BH provides no shortcuts to avoid shortcut conflicts, but you can view the included `Example.sublime-keymaps` file to get an idea how to set up your own.
