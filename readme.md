# Table of Contents
- [About](#about)
    - [Sublime Text 3 Support?](#sublime-text-3-support)
    - [Overview](#overview)
- [Feature List](#feature-list)
- [General Use](#general-use)
    - [Built-in Supported brackets](#built-in-supported-brackets)
    - [Additional Features](#additional-features)
    - [Bracket Plugin](#bracket-plugin)
    - [Shortcuts](#shortcuts)
- [Customizing BracketHighligher](#costumizing-brackethighlighter)
    - [Configuring Brackets](#cnfiguring-brackets)
    - [Configuring Highlight Style](#configuring-highlight-style)
- [Bracket Plugin API](#bracket-plugin-api)
    - ['Defintion' Plugins](#definition-plugins)
    - [Run Instance Plugins](#run-instance-plugins)
- [Credits](#credits)
- [Changelog](#changelog)

# About
This is a fork of pyparadigm's _SublimeBrackets_ and _SublimeTagmatcher_ (both are no longer available).  I forked this to fix some issues I had and to add some features I wanted.  I also wanted to improve the efficiency of the matching.  This cuts down on the parallel searching that is now streamlined in one search.  Since then, I have rewritten the entire code base to bring more flexibility, speed, and features.

<img src="http://dl.dropbox.com/u/342698/BracketHighlighter/Example1.png" border="0">

## Sublime Text 3 Support?
ST3 support is found here (at the present time):  https://github.com/facelessuser/BracketHighlighter/tree/BH2ST3

## Overview
Bracket Highlighter matches a variety of brackets such as: ```[]```, ```()```, ```{}```, ```""```, ```''```, ```<tag></tag>```, and even custom brackets.

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
- Bracket plugins that can jump between bracket ends, select content, remove brackets and/or content, wrap selectios with brackets, swap brackets, swap quotes (handling quote escaping between the main quotes), fold/unfold conent between brackets, toggle through tag attribute selecection, select both the opening and closing tag name to change both simultaneously.

# General Use
In general, BracketHighligher (BH) will highlight brackets (or defined bracket like start and end blocks) surrounding the cursor.  By default, BH will put opening and closing icons in the gutter of the corresponding line containing open or closising bracket. BH, by default, will underline the closing and opening bracket as well.

## Built-in Supported brackets
Currently BH supports the following brackets out of the box:

- round
- square
- curly
- angle
- single and double quotes
- python single and double quotes (unicode and raw)
- python tripple single and double quotes (unicode and raw)
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

BH also supports highlighting basic sub brackets ```(), [], {}``` within supported regex and strings.

## Additional Features
BH has a couple of additonal features built-in.

### Toggle Global Enable (bh_toggle_enable)
This command enables and disables BH globally

### Toggle String Bracket Escape Mode (bh_toggle_string_escape_mode)
This toggles BH's recognition mode of escaped sub brackets in strings and regex.  The modes are string escape mode and regex escape mode.

### Settings
When changing settings, you should copy the entire ```bh_core.sublime-settings``` to your ```User``` folder before changing.  Style and color will be discussed in greater depth in the ```Configuring Highlight Style``` section.

These are the basic settings you can change:
```javascript
    //Debug logging
    "debug_enable": false,

    // When only either the left or right bracket can be found
    // this defines if the unmatched bracket should be shown.
    "show_unmatched" : true,

    // High visibilty style and color for high visibility mode
    // (solid|outline|underline)
    "high_visibility_style": "outline",
    // (scope|__default__|__bracket__)
    "high_visibility_color": "__bracket__",

    // Match brackets only when the cursor is touching the inside of the bracket
    "match_only_adjacent": false,

    // Character threshold to search
    "search_threshold": 5000,

    // Set mode for string escapes to ignore (regex|string)
    "bracket_string_escape_mode": "string",

    // Set max number of multi-select brackets that will be searched automatically
    "auto_selection_threshold" : 10,

    // Disable gutter icons when doing multi-select
    "no_multi_select_icons": false,
```

### Bracket Plugins
Bh is also extendable via plugins and provides an number of plugins by default.  See [Bracket Plugins](#bracket-plugins) to learn more about the included plugins.

## Bracket Plugin
BH provides a number of built in Bracket Plugins that take advantage of BH's matching to provide additional features.  Most plugin features are available via the Tools->Packages->BracketHighlighter menu or the command palette.  To see how to configure shortcuts, see the ```Example.sublime-settings``` file.

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

Additional tag settings found in ```bh_core.sublime-settings```:
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
Wrap the current selection with supported bracket of your choice.  Wrapping definitions are configured in ```bh_wrapping.sublime-settings```.

### Bracket Swapping Plugin
Swap the current surrounding bracket with supported bracket of your choice.  Swapping definitions are configured in ```bh_swapping.sublime-settings```.

## Shortcuts
By default BH provides no shortcuts to avoid shortcut conflicts, but you can view the included ```Example.sublime-keymaps``` file to get an idea how to set up your own.

# Customizing BracketHighligher
BH is extremely flexible and be customized and extended to fit a User's needs.  The first step is to copy the ```bh_core.sublime-settings``` to your ```User``` folder.

## Configuring Brackets
BH has been written to allow users to define any brackets they would like to have highlighted.  There are two kinds of brackets you can define: ```scope_brackets``` (search file for scope regions and then use regex to test for opening and closing brackets) and ```brackets``` (use regex to find opening and closing brackets).  ```bracket``` should usually be the preferred type.  ```scope_brackets``` are usually used for brackets whose opening and closing are the same and not distinguishable form one another by regex; scope brackets must be contained in a continuous scope region like string for quotes etc.

### Configuring Brackets
Brackets are defined under ```brackets``` in ```bh_core.sublime-settings```.

Angle and Curly bracket will be used as an eample (not all options may be shown in these examples):

```javascript
        {
            "name": "angle",
            "open": "(<)",
            "close": "(>)",
            "style": "angle",
            "scope_exclude": ["string", "comment", "keyword.operator"],
            "language_filter": "whitelist",
            "language_list": ["HTML", "HTML 5", "XML", "PHP", "HTML+CFML", "ColdFusion", "ColdFusionCFC"],
            "plugin_library": "bh_modules.tags",
            "enabled": true
        },
        {
            "name": "curly",
            "open": "(\\{)",
            "close": "(\\})",
            "style": "curly",
            "scope_exclude": ["string", "comment"],
            "scope_exclude_exceptions": ["string.other.math.block.environment.latex"],
            "language_filter": "blacklist",
            "language_list": ["Plain text"],
            "find_in_sub_search": "true",
            "ignore_string_escape": true,
            "enabled": true
        },
```

- **name**: the name of the bracket (should be unique)
- **open**: defines the opening bracket (one and only one captureing group must be present)
- **close**: defines the closing bracket (one and only one captureing group must be present)
- **style**: Name of style definition to be used to highlight the brackets.  See ```Configuring Bracket Styles``` for more info.
- **scope_exclude**: Scopes where the opening and closing brackets should be ignored.
- **language_filter**: This works in conjunction with ```language_list```.  It specifies whether ```language_list``` is a ```blacklist``` or ```whitelist```.
- **language_list**: an array of tmLanguage file names that should be avoided or included for highlighting.  Looks to ```language_filter``` to determine if avoidance or inclusion is used.
- **enabled**: disable or enable rule
- **scope_exclude_exceptions (optional)***: used to ignore exluding of sub scopes such as in the curly example above where ```string``` is excluded, but not ```string.other.math.block.environment.latex```.
- **plugin_library (optional)**: defines plugin to use for determining matches (see Bracket Plugin API for more info on matching plugins)
- **find_in_sub_search (optional)**: this rule should be included when doing sub bracket matching in ```scope_brackets``` (like finding round brackets between quotes etc.).  The setting must be as string and can be either (true|false|only); only means this bracket is only matched as a sub bracket of a ```scope_bracket```.
- **ignore_string_escape (optional)**: Do not ignore sub brackets found in strings and regex when escaped, but use internal escape logic to determine if the brackets should be ignored based on whether regex or string escape mode is set.

### Configuring Scope Brackets
Scope Brackets are defined under ```scope_brackets``` in ```bh_core.sublime-settings```.

Python Single Quote bracket will be used as an eample (not all options are shown in this example):

```javascript
        {
            "name": "py_single_quote",
            "open": "u?r?((?:'')?')",
            "close": "((?:'')?')",
            "style": "single_quote",
            "scopes": ["string"],
            "language_filter": "whitelist",
            "language_list": ["Python"],
            "sub_bracket_search": "true",
            "enabled": true
        },
```

- **name**: the name of the bracket (should be unique)
- **open**: defines the opening bracket (one and only one captureing group must be present)
- **close**: defines the closing bracket (one and only one captureing group must be present)
- **style**: Name of style definition to be used to highlight the brackets.  See ```Configuring Bracket Styles``` for more info.
- **scopes**: scope that should be searched to find the opening and closing brackets.
- **language_filter**: This works in conjunction with ```language_list```.  It specifies whether ```language_list``` is a ```blacklist``` or ```whitelist```.
- **language_list**: an array of tmLanguage file names that should be avoided or included for highlighting.  Looks to ```language_filter``` to determine if avoidance or inclusion is used.
- **sub_bracket_search**: should this scope bracket also search for sub brackets (like curly brackets in strings etc.).
- **enabled**: disable or enable rule
- **plugin_library (optional)**: defines plugin to use for determining matches (see Bracket Plugin API for more info on matching plugins)

## Configuring Highlight Style
Each bracket definition (described in [Configuring Scope Brackets](#configuring-scope-brackets) and [Configuring Brackets](#configuring-brackets)) has a ```style``` setting that you give a style definition to.  Style definitions are defined under ```bracket_styles``` in ```bh_core.sublime-settings```.

There are two special style definitions whose names are reserved: ```default``` and ```unmatched```, but you can configure them.  All other custom style definitions follow the same pattern (see ```curly``` below and compare to the special style defintions; format is the same)  All custom styles follow this pattern.  See description below:

```javascript
        // "default" style defines attributes that
        // will be used for any style that does not
        // explicitly define that attribute.  So if
        // a style does not define a color, it will
        // use the color from the "default" style.
        "default": {
            "icon": "dot",
            "color": "brackethighlighter.default",
            "style": "underline"
        },

        // This particular style is used to highlight
        // unmatched bracekt pairs.  It is a special
        // style.
        "unmatched": {
            "icon": "question",
            // "color": "brackethighlighter.unmatched",
            "style": "outline"
        },
        // User defined region styles
        "curly": {
            "icon": "curly_bracket"
            // "color": "brackethighlighter.curly",
            // "style": "underline"
        },
```

- **icon**: icon to show in gutter. Available options are (angle|round|curly|square|tag|star|dot|bookmark|question|quote|double_quote|single_quote|single_quote_offset|
double_quote_offset|none)
- **color**: scope to define color
- **style**: higlight style.  Available options are (solid|outline|underline|none)

As shown in the example above, if an option is omitted, it will use the setting in ```default```.  So ```curly```, in this example, defines ```icon```, but will use ```default``` for the ```color``` and ```style```.

To customize the color for ```curly``` you can create your own custom scope.

Add this to your color scheme:
```XML
        <dict>
            <key>name</key>
            <string>Bracket Curly</string>
            <key>scope</key>
            <string>brackethighlighter.curly</string>
            <key>settings</key>
            <dict>
                <key>foreground</key>
                <string>#CC99CC</string>
            </dict>
        </dict>
```

And then use the scope:
```javascript
        "curly": {
            "icon": "curly_bracket"
            "color": "brackethighlighter.curly",
            // "style": "underline"
        },
```

# Bracket Plugin API
There are two kinds of plugins that can be written ```definition``` plugins (plugins attached to bracket definitions via the ```plugin_library``` option) or ```run instance``` plugins (plugins that are that are fed in the BracketHighligher via the command parameter ```plugin```).

Bracket plugins use ```BracketRegions```. ```BracketRegions``` are simple objects containing a begin pt and end pt of a bracket.

Class:

- **BracketRegion(begin_pt, end_pt)**

Attributes of BracketRegion:

- **begin**: the start pt of the BracketRegion
- **end**: the end pt of the BracketRegion

Methods of BracketRegion:

- **size()**: returns size of region
- **move(begin_pt, end_pt)**: returns a new BracketRegion object with the points moved as specified by the parameters
- **toregion**: returns a sublime Region() object

## 'Defintion' Plugins
These are plugins that are attached to the bracket definition and aid in processing the brackets.  These kids of plugins have two methods you can provide ```post_match``` and/or ```compare```.

### compare
```compare``` is run when comparing the opening bracket with closing brackets.  This allows you to provide logic to accept or reject the pairing of an opening bracket with a closing bracket.  You should not change the text in the view during this operation.

The ```compare``` method receives the following paramters:

- **name**: the name of the bracket definition being evaluated
- **first**:  a bracket region for the opening bracket
- **second**: a bracket region for the closing bracket
- **bfr**: the file buffer

Returns:

- **Boolean**: indicating whether the the comparison yields a suitable match

Example (from phphekywords.py):
```python
def compare(name, first, second, bfr):
    return "end" + bfr[first.begin:first.end].lower() == bfr[second.begin:second.end].lower()
```

### post_match
```post_match``` is run after the brackets have been matched.  You can do things like alter the highlighting region and change the bracket_style if needed. You should not change the text in the view during this operation.

The ```post_match``` method receives the following parameters:

- **name**: the name of the bracket definition being evaluated
- **style**: the style definition name that is to be used to highlight the region
- **first**:  a bracket region for the opening bracket
- **second**: a bracket region for the closing bracket
- **center**: position (pt) of cursor (in retrospect, probably not the most intuitive name; not sure why I named it such)
- **bfr**: the file buffer
- **threshold**: the calculated search window of the buffer that is being searched

Returns:

- **BracketRegion**: opening bracket region
- **BracketRegion**: closing bracekt region
- **style**: the name of the style definition to use

Example (from rubykeywords.py):
```python
import re


def post_match(view, name, style, first, second, center, bfr, threshold):
    if first is not None:
        # Strip whitespace from the beginning of first bracket
        open_bracket = bfr[first.begin:first.end]
        if open_bracket != "do":
            m = re.match(r"^(\s*\b)[\w\W]*", open_bracket)
            if m:
                first = first.move(first.begin + m.end(1), first.end)
    return first, second, style
```

Example (snippet from tags.py)
```python
def post_match(view, name, style, first, second, center, bfr, threshold):
    left, right = first, second
    threshold = [0, len(bfr)] if threshold is None else threshold
    tag_settings = sublime.load_settings("bh_core.sublime-settings")
    tag_mode = get_tag_mode(view, tag_settings.get("tag_mode", {}))
    tag_style = tag_settings.get("tag_style", "angle")
    bracket_style = style

    if first is not None and tag_mode is not None:
        matcher = TagMatch(view, bfr, threshold, first, second, center, tag_mode)
        left, right = matcher.match()
        if not matcher.no_tag:
            bracket_style = tag_style

    return left, right, bracket_style
```

## Run Instance Plugins
```Run instance``` plugins are fed into the command executing a BracketHighlighter match via the ```plugin``` parameter.

Example of run instance plugin getting called:
```javascript
// Go to left bracket
    {
        "caption": "BracketHighlighter: Jump to Left Bracket",
        "command": "bh_key",
        "args":
        {
            "lines" : true,
            "plugin":
            {
                "type": ["__all__"],
                "command": "bh_modules.bracketselect",
                "args": {"select": "left"}
            }
        }
    },
```

The ```plugin``` paramter is a dictionary that contains 3 parameters to define what plugin should get run, with what arguments, and on what bracket defintion.

- **type**: an array containing the bracket definition names that the plugin should be run on.  Use ```__all__``` for all bracket definitions.
- **command**: the plugin to run.  For internal plugins, they are referenced by ```bh_modules.<plugin name>```.  For custom plugins, you should use the folder path releative to ```Packages```.  So if I had a plugin called ```myplugin.py``` in my ```User``` folder, I would use ```User.myplugin```.
- **args**: a dictionary contianing the arguments to feed into the plugin.

You create ```run instance``` plugins by deriving a class from the ```BracketPluginCommand``` class.  Then you provide a method called ```plugin``` that returns the class.

Class:

- **BracketPluginCommand()**

Parameters of BracketPluginCommand:

- **edit**: sublime edit object
- **name**: name of tag definition being evaluated

Attributes of BracketPluginCommand:

- **view**: the sublime view containg the bracket (don't change this)
- **left**:  a bracket region for the opening bracket (can be changed)
- **right**: a bracket region for the closing bracket (can be changed)
- **selection**: an array containing the selection that triggered the match (can be changed)

Methods of BracketPluginCommand:

- **run(edit, name, <args>)**: (edit is a sublime edit object and name is the bracket definition being evaluated)

Example (from foldbracket.py):
```python
import BracketHighlighter.bh_plugin as bh_plugin
import sublime


class FoldBrackets(bh_plugin.BracketPluginCommand):
    def run(self, edit, name):
        content = sublime.Region(self.left.end, self.right.begin)
        new_content = [content]
        if content.size() > 0:
            if self.view.fold(content) == False:
                new_content = self.view.unfold(content)
        self.selection = new_content


def plugin():
    return FoldBrackets
```

# Credits
- pyparadigm: for his original efforts with SublimeBrackets and SublimeTagmatcher which originally BracketHighlighter was built off of and the inspiration behind the current implementation.
- BoundInCode: for his Tag icon

# Changelog

#### Version 2.0.0
- Re-write of BracketHighlighter

#### Older Versions
- See [Complete Changelog](https://github.com/facelessuser/BracketHighlighter/blob/BH2/CHANGELOG.md)
