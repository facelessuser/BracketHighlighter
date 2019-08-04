# Basic Usage

## Overview

Out of the box, BH will highlight brackets (or defined brackets like start and end blocks) surrounding the cursor.  BH will also put opening and closing icons in the gutter of the corresponding line containing open or closing bracket.

It is advised that you disable Sublime's default bracket and tag matcher in your `Preferences.sublime-settings` file or you will have matching conflicts:

```js
    "match_brackets": false,
    "match_brackets_angle": false,
    "match_brackets_braces": false,
    "match_brackets_content": false,
    "match_brackets_square": false,
    "match_tags": false
```

If you are using Sublime Text build 3124+, a new feature has been added which shows a popup when you mouse over a bracket that has its matching bracket pair off screen.  It will show where the other bracket is located with line context and provide a link to jump to the other bracket.  When mousing over a bracket in which the match could not be found, a popup explaining why this might occur will be shown and give the option to click a link which will perform a search without thresholds to see if it can find the brackets when restraints are removed.

## Built-in Supported brackets

BH supports a variety of brackets out of the box; here are some examples:

- round
- square
- curly
- angle
- single and double quotes
- Python single, double, and triple quotes (Unicode and raw)
- Django Python templates with mixed HTML, CSS, and JavaScript
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

`bh_toggle_string_escape_mode` toggles BH's recognition mode of escaped sub brackets in strings and regex.  The modes are *string escape* mode and *regex escape* mode.

### Find Matching Offscreen Brackets

When `show_offscreen_bracket_popup` is enabled, mousing over an on screen bracket, or invoking the `bh_offscreen_popup` command, will show a popup on the screen that reveals the location of the matching offscreen bracket(s) (only available for Sublime Text 3 versions that support this).  The cursor needs to be between a matching pair of brackets.

## Bracket Plugin Commands

BH is also extendable via plugins and provides a number of built-in Bracket Plugins that take advantage of BH's matching to provide additional features.  Most plugin features are available via the command palette.  To see how to configure shortcuts, see the [`Example.sublime-keymap`][keymap] file.

### Bracket Select Plugin

The Bracket Select plugin selects the content between the brackets or moves the selection to the opening or closing bracket.  Behavior is slightly modified for tags.

### Swap Brackets Plugin

The Swap Brackets plugin can swap the current brackets to another type of bracket.  When selected, it will displays the bracket options that are allowed for the current language.  Allowed brackets are defined in `bh_swapping.sublime-settings`.

### Wrap Brackets Plugin

The Wrap Brackets plugin wraps selected text with a bracket pair.  When selected, it will display the bracket options that are allowed for the current language.  Allowed brackets are defined in `bh_wrapping.sublime-settings`.

### Bracket Remove Plugin

The Bracket Remove plugin removes the surrounding brackets around the cursor.

### Fold Bracket Plugin

The Fold Bracket plugin folds the content of the current surrounding brackets.

### Swap Quotes Plugin

The Swaps Quotes plugin swaps the quote style of surrounding quotes from double to single or vice versa.  It also handles escaping and un-escaping of sub quotes.

### Tag Plugin

The Tag plugin Provides extra logic to target and highlight XML/HTML tags.  To use BH's built-in HTML highlighting in your HTML-like template language of choice, add it to the list in `bh_tag.sublime_settings`.

### Tag Attribute Select Plugin

The Tag Attribute plugin can cycle through the tag attributes of the selected tag.

### Tag Name Select Plugin

Tag Name Select plugin selects the opening and closing tag name of the current selected tag.

## Keyboard Shortcuts

BH provides no keyboard shortcuts in order to avoid shortcut conflicts, but you can view the included [`Example.sublime-keymap`][keymap] file to get an idea how to set up your own.

--8<-- "refs.md"
