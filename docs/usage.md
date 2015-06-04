# User Guide {: .doctitle}
How to use BracketHighlighter.

---

## General Use
In general, BracketHighlighter (BH) will highlight brackets (or defined bracket like start and end blocks) surrounding the cursor.  By default, BH will put opening and closing icons in the gutter of the corresponding line containing open or closing bracket. BH, by default, will underline the closing and opening bracket as well.

## Built-in Supported brackets
Currently BH supports the following brackets out of the box:

- round
- square
- curly
- angle
- single and double quotes
- python single and double quotes (Unicode and raw)
- python triple single and double quotes (Unicode and raw)
- JavaScript regex
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

## General Commands
BH has a couple of additional features built-in which are found in the command palette.

### Toggle Global Enable
The `bh_toggle_enable` command enables and disables BH globally.

### Toggle String Bracket Escape Mode
`bh_toggle_string_escape_mode` toggles BH's recognition mode of escaped sub brackets in strings and regex.  The modes are string escape mode and regex escape mode.

## Bracket Plugin Commands
BH is also extendable via plugins and provides a number of built in Bracket Plugins that take advantage of BH&rsquo;s matching to provide additional features.  Most plugin features are available via the `Tools->Packages->BracketHighlighter` menu or the command palette.  To see how to configure shortcuts, see the `Example.sublime-settings` file.

### Bracket Select Plugin
This plugin changes the selection inside between the brackets.  It can select the content or move the bracket to the opening or closing bracket.  Behavior is slightly modified for tags.

### Swap Brackets Plugin
This plugin allows the swapping of the current brackets to another type of bracket.  When selected, it will displayed the bracket options that allowed for the current language.  Allowed brackets are defined in `bh_swapping.sublime-settings`.

### Wrap Brackets Plugin
This plugin allows the wrapping of selected text with a bracket pair.  When selected, it will displayed the bracket options that allowed for the current language.  Allowed brackets are defined in `bh_wrapping.sublime-settings`.

### Bracket Remove Plugin
Removes the surrounding brackets.

### Fold Bracket Plugin
Folds the content of the current surrounding brackets.

### Swap Quotes Plugin
Swap the quotes style of surrounding quotes from double to single or vice versa.  It also handles escaping and un-escaping of sub quotes.

### Tag Plugin
Plugin used to help highlight XML/HTML tags.

### Tag Attribute Select Plugin
Cycle through selecting tag attributes of tags.

### Tag Name Select Plugin
Select the opening and closing tag name of current tag.

### Bracket Swapping Plugin
Swap the current surrounding bracket with supported bracket of your choice.  Swapping definitions are configured in `bh_swapping.sublime-settings`.

## Shortcuts
By default BH provides no shortcuts to avoid shortcut conflicts, but you can view the included `Example.sublime-keymaps` file to get an idea how to set up your own.

*[BH]: BracketHighlighter
*[ST2]: Sublime Text 2
*[ST3]: Sublime Text 3
