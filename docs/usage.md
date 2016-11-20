# Basic Usage {: .doctitle}
How to use BracketHighlighter.

---

## General Use
In general, BracketHighlighter (BH) will highlight brackets (or defined brackets like start and end blocks) surrounding the cursor.  By default, BH will put opening and closing icons in the gutter of the corresponding line containing open or closing bracket.

It is advised that you disable Sublime's default bracket and tag matcher in your `Preferences.sublime-settings` file or you will have matching conflicts:

```js
    "match_brackets": false,
    "match_brackets_angle": false,
    "match_brackets_braces": false,
    "match_brackets_content": false,
    "match_brackets_square": false,
    "match_tags": false
```

If you are using Sublime Text build 3116+, a new feature has been added which shows a popup when you mouse over a bracket that has its matching bracket pair off screen.  It will show where the other bracket is located with line context and and provide a link to jump to the other bracket.  When mousing over a bracket in which the match could not be found, a popup explaining why this might be will show up giving you the option to click a link which will perform a search without thresholds to see if it can find the brackets when restraints are removed.

## Built-in Supported brackets
BH supports a variety of brackets out of the box; here are some examples:

- round
- square
- curly
- angle
- single and double quotes
- Python single, double, and triple quotes (Unicode and raw)
- Django Python templates with mixed HTML, CSS, and JS
- JavaScript regex
- Perl regex
- Ruby regex
- Markdown bold, italic, and code blocks
- CSSedit groups
- Ruby conditional statements
- C/C++ compiler switches
- PHP conditional keywords
- PHP angle brackets `<?php ?>`
- Erlang conditional statements
- HTML, ColdFusion, XML, and various other template tags
- Bash conditional and looping constructs
- Fish conditional and looping constructs
- Lua
- Pascal
- Elixir

Within supported regex and strings, BH can also highlight basic sub brackets between the matched quotes: `(), [], {}`.

## General Commands
BH has a couple of additional features built-in which are found in the command palette.

### Toggle Global Enable
The `bh_toggle_enable` command enables and disables BH globally.

### Toggle String Bracket Escape Mode
`bh_toggle_string_escape_mode` toggles BH's recognition mode of escaped sub brackets in strings and regex.  The modes are 'string escape' mode and 'regex escape' mode.

### Find Matching Offscreen Bracket
When the setting `show_offscreen_bracket_popup` is enabled, the `bh_offscreen_popup` command shows a popup on the screen showing the location of the matching offscreen bracket(s) (only available for Sublime Text 3 versions that support this).  Cursor needs to be between a matching pair of brackets.  The popup will also auto popup when the mouse hovers over an onscreen bracket when the other matching bracket is offscreen.

## Bracket Plugin Commands
BH is also extendable via plugins and provides a number of built in Bracket Plugins that take advantage of BH&rsquo;s matching to provide additional features.  Most plugin features are available via the `Tools->Packages->BracketHighlighter` menu or the command palette.  To see how to configure shortcuts, see the `Example.sublime-settings` file.

### Bracket Select Plugin
Selects the content between the brackets or moves the selection to the opening or closing bracket.  Behavior is slightly modified for tags.

### Swap Brackets Plugin
Allows the swapping of the current brackets to another type of bracket.  When selected, it will displayed the bracket options that allowed for the current language.  Allowed brackets are defined in `bh_swapping.sublime-settings`.

### Wrap Brackets Plugin
Allows the wrapping of selected text with a bracket pair.  When selected, it will display the bracket options that are allowed for the current language.  Allowed brackets are defined in `bh_wrapping.sublime-settings`.

### Bracket Remove Plugin
Removes the surrounding brackets.

### Fold Bracket Plugin
Folds the content of the current surrounding brackets.

### Swap Quotes Plugin
Swaps the quote style of surrounding quotes from double to single or vice versa.  It also handles escaping and un-escaping of sub quotes.

### Tag Plugin
Provides extra logic to target and highlight XML/HTML tags.  To use BracketHighlighter's built-in HTML highlighting in your HTML-like template language of choice, add it to the list in `bh_tag.sublime_settings`.

### Tag Attribute Select Plugin
Cycles through selecting tag attributes.

### Tag Name Select Plugin
Selects the opening and closing tag name of current tag.

### Bracket Swapping Plugin
Swaps the current surrounding bracket with different supported brackets of your choice.  Swapping definitions are configured in `bh_swapping.sublime-settings`.

## Shortcuts
BH provides no shortcuts in order to avoid shortcut conflicts, but you can view the included `Example.sublime-keymaps` file to get an idea how to set up your own.

*[BH]: BracketHighlighter
*[ST2]: Sublime Text 2
*[ST3]: Sublime Text 3

## Suggested User Settings
```js
"match_brackets": false // disable default ST bracket highlighting
```
