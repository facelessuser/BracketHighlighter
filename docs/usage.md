# User Guide {: .doctitle}
How to use BracketHighlighter.

---

# General Use
In general, BracketHighlighter (BH) will highlight brackets (or defined bracket like start and end blocks) surrounding the cursor.  By default, BH will put opening and closing icons in the gutter of the corresponding line containing open or closing bracket. BH, by default, will underline the closing and opening bracket as well.

# Built-in Supported brackets
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

# General Commands
BH has a couple of additional features built-in.

## Toggle Global Enable
The `bh_toggle_enable` command enables and disables BH globally.

## Toggle String Bracket Escape Mode
`bh_toggle_string_escape_mode` toggles BH's recognition mode of escaped sub brackets in strings and regex.  The modes are string escape mode and regex escape mode.

# Bracket Plugin Commands
BH is also extendable via plugins and provides a number of built in Bracket Plugins that take advantage of BH&rsquo;s matching to provide additional features.  Most plugin features are available via the `Tools->Packages->BracketHighlighter` menu or the command palette.  To see how to configure shortcuts, see the `Example.sublime-settings` file.

## Bracket Select Plugin
This plugin changes the selection inside between the brackets.  It can select the content or move the bracket to the opening and closing bracket.  Behavior is slightly modified for tags.

## Swap Brackets Plugin
This plugin allows the current brackets to another type of bracket.  See [Wrapping and Swapping Commands](#wrapping-and-swapping-commands) for more info.

## Bracket Remove Plugin
Removes the surrounding brackets.

## Fold Bracket Plugin
Folds the content of the current surrounding brackets.

## Swap Quotes Plugin
Swap the quotes style of surrounding quotes from double to single or vice versa.  It also handles escaping and unescaping of sub quotes.

## Tag Plugin
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

## Tag Attribute Select Plugin
Cycle through selecting tag attributes of tags.

## Tag Name Select Plugin
Select the opening and closing tag name of current tag.

## Bracket Wrapping Plugin
Wrap the current selection with supported bracket of your choice.  Wrapping definitions are configured in `bh_wrapping.sublime-settings`.

## Bracket Swapping Plugin
Swap the current surrounding bracket with supported bracket of your choice.  Swapping definitions are configured in `bh_swapping.sublime-settings`.

# Wrapping and Swapping Commands
BH provides a way to wrap content with brackets or swap brackets.

## Swapping Brackets
Bracket swapping support utilizes the `swapbrackets` bh_plugin to swap out the current highlighted brackets with another set of pre-defined brackets.  Allowed brackets are defined in the `bh_swapping.sublime-settings` file.  Swap rules are found under the key `swapping` where `swapping` is an array of language swap rules.

```js
    "swapping": [
        {
            "enabled": true,
            "language_list": ["C++", "C"],
            "language_filter": "whitelist",
            "entries": [
                {"name": "C/C++: #if", "brackets": ["#if ${BH_SEL}", "#endif"]},
                {"name": "C/C++: #if, #else", "brackets": ["#if${BH_SEL}", "#else\n${BH_TAB:/* CODE */}\n#endif"]},
                {"name": "C/C++: #if, #elif", "brackets": ["#if${BH_SEL}", "#elif ${BH_TAB:/* CONDITION */}\n${BH_TAB:/* CODE */}\n#endif"]},
                {"name": "C/C++: #ifdef", "brackets": ["#ifdef${BH_SEL}", "#endif"]},
                {"name": "C/C++: #ifdef, #else", "brackets": ["#ifdef${BH_SEL}", "#else\n${BH_TAB:/* CODE */}\n#endif"]},
                {"name": "C/C++: #ifndef", "brackets": ["#ifndef${BH_SEL}", "#endif"]},
                {"name": "C/C++: #ifndef, #else", "brackets": ["#ifndef${BH_SEL}", "#else\n${BH_TAB:/* CODE */}\n#endif"]}
            ]
        }
    ]
```

Each language rule contains the following attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| enabled | bool | Specifies if the rule is enabled. |
| language_list | [string] | An array of languages. |
| language_filter | string | A string that specifies if the `language_list` is either a `whitelist` or `blacklist`. |
| entries | [dict] | An array of dictionaries, where each dictionary describes a type of bracket that can be swapped to. |

Within the language rules under `entries`, swap entries are defined.  Each entry represents a bracket you can swap to.

| Entry | Type | Description |
|-------|------|-------------|
| name | string | The name of the entry as it will be seen in the command palette. |
| brackets | [string] | An array consisting of a string that represents the opening bracket and a string that represents the closing bracket. |

Within the `brackets`, you can specify the where the cursor(s) will appear by using `${BH_SEL}`  If you would like the selection to display text as a hint to what a user should enter in the selection, you can use `${BH_SEL:optional text}`.

Within the `brackets`, you can also define tab stops that a user can tab through and enter text.  The tab stop syntax is `${BH_TAB}`.  You can also define optional text within a tab stop to give the user a hint of what should be entered in at the tab stop using the following syntax `${BH_TAB:optional text}`.

## Wrapping Brackets
BH has a special command for wrapping selected text in pre-defined brackets.  Allowed brackets are defined in the `bh_wrapping.sublime-settings` file.  Wrap rules are found under the key `wrapping` where `wrapping` is an array of language wrap rules.

```js
    "wrapping": [
        {
            "enabled": true,
            "language_list": ["Plain text"],
            "language_filter": "blacklist",
            "entries": [
                {"name": "{} Curly", "brackets": ["{", "}${BH_SEL}"], "insert_style": ["inline", "block", "indent_block"]}
            ]
        }
    ]
```

Each language rule contains the following attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| enabled | bool | Specifies if the rule is enabled. |
| language_list | [string] | An array of languages. |
| language_filter | string | A string that specifies if the `language_list` is either a `whitelist` or `blacklist`. |
| entries | [dict] | An array of dictionaries, where each dictionary describes a type of bracket that can be used to wrap the selection. |

Within the language rules under `entries`, wrap entries are defined.  Each entry represents a bracket you can wrap the selection with.

| Entry | Type | Description |
|-------|------|-------------|
| name | string | The name of the entry as it will be seen in the command palette. |
| brackets | [string] | An array consisting of a string that represents the opening bracket and a string that represents the closing bracket. |
| insert_style | [string] | An array consisting of allowed insertion styles.  Allowed insertion styles are: `inline`, `block`, and `indent_block`.  Default is `#!js ['inline']`. |

Within the `brackets`, you can specify the where the cursor(s) will appear by using `${BH_SEL}`  If you would like the selection to display text as a hint to what a user should enter in the selection, you can use `${BH_SEL:optional text}`.

Within the `brackets`, you can also define tab stops that a user can tab through and enter text.  The tab stop syntax is `${BH_TAB}`.  You can also define optional text within a tab stop to give the user a hint of what should be entered in at the tab stop using the following syntax `${BH_TAB:optional text}`.

# Shortcuts
By default BH provides no shortcuts to avoid shortcut conflicts, but you can view the included `Example.sublime-keymaps` file to get an idea how to set up your own.

*[BH]: BracketHighlighter
*[ST2]: Sublime Text 2
*[ST3]: Sublime Text 3
