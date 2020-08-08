# BracketHighlighter

## 2.28.1

- **FIX**: Handle HTML attributes even when there are no spaces between them.

## 2.28.0

- **NEW**: Rename `language_filter` options `whitelist` and `blacklist` to `allowlist` and `blocklist` respectively.
- **NEW**: Add global option `gutter_icons` to control enabling or disabling icons.

## 2.27.10

- **FIX**: Handle certain regular expression compilation failures in a more graceful way.

## 2.27.9

- **FIX**: Remove old clone workaround as this issue will be fixed upstream in Sublime Text 4 builds.

## 2.27.8

- **FIX**: Content align bug.

## 2.27.7

- **FIX**: Update support to include OCaml comment support.
- **FIX**: Fix avoiding round brackets in shell case statements.
- **FIX**: Thread adjustments that allow BracketHighlighter to go completely idle when Sublime Text is idle.
- **FIX**: Fix Ruby interpolated strings.
- **FIX**: Fix optional tags for `option` and `optgroup`.

## 2.27.6

- **FIX**: Fix issue where HTML style attribute quotes where not highlighted due to syntax definition changes.
- **FIX**: Add support for `@` in HTML attributes.

## 2.27.5

- **FIX**: Fix issue where bracket context code blocks in popups sometimes are recognized as Jinja2 template variables.
- **FIX**: Fix internal clone view cleanup.
- **FIX**: Fix bad clone reference.
- **FIX**: `on_hover` should not occur if `bracket_highlighter.ignore` is set in the view.

## 2.27.4

- **FIX**: Avoid targeting common `HERDOC` syntax with angle brackets. #482

## 2.27.3

- **FIX**: Selecting "no threshold" search from popup quickly reverts back to unmatched.
- **FIX**: Backtick string support extended to JavaScript.

## 2.27.2

- **FIX**: `C#` interpolated strings !468.
- **FIX**: Fix C/C++ preprocessor highlighting !474.
- **FIX**: Only highlight the keyword in C/C++ preprocessors af22600cd23bd3c15a1a0f6fc54041e6d96b3dd3.

## 2.27.1

- **FIX**: Fix Lua loops by avoiding `while` and `from` and just highlighting `do` #466.

## 2.27.0

- **NEW**: Add option to always show the bracket popup on bracket hover #457.
- **FIX**: Fix clone views not properly supported #454.
- **FIX**: Improvements to Ruby conditional matching #452.

## 2.26.0

- **NEW**: Added new configuration `user_bracket_styles` to allow a user to override specific rules or just part of a  
specific rule instead of copying all of `bracket_styles` #448.
- **NEW**: Add colorization with region-ish scopes for Sublime builds 3148+ #448.
- **FIX**: Ruby issue with conditionals immediately followed after return keyword #425.
- **FIX**: PHP issue for arrows (`$var->prop`) #446.

## 2.25.2

- **FIX**: Update tag attribute pattern.
- **FIX**: Add SVG self closing tags.
- **FIX**: Temporarily use `thin_underline` style to mitigate issue #443.

## 2.25.1

- **FIX**: Update dependencies.

## 2.25.0

- **FIX**: Quick start image links.
- **FIX**: Allow Markdown related brackets to work in Markdown Extended.
- **FIX**: Allow `HTML (Jinja2)` to work in HTML.
- **NEW**: Add Markdown `` ` `` to swap and wrap.
- **NEW**: Add commonly used commands to the command panel (documents and settings) #419.

## 2.24.2

- **FIX**: Avoid things like `->` in PHP due to new Sublime default syntax changes #417.
- **FIX**: Add support for Python f-strings.

## 2.24.1

- **FIX**: Random regions failure.
- **FIX**: Lua keyword match at beginning of line.

## 2.24.0

- **NEW**: Popup/Phantom support limited to 3124+ moving forward to prepare for `mdpopups` 2.0 that will drop legacy  
support for old, early implementation of popups and phantoms.
- **NEW**: No longer try and force dependency updates.  Leave it up to Package Control (whether they do it or not).
- **NEW**: CSS adjustments to popups.
- **FIX**: Fix tag matching corner case #409.

## 2.23.3

- **FIX**: Fix error `ImportError: No module named 'yaml'` #400.

## 2.23.2

- **FIX**: Add backtick quote support for ruby and shell script syntaxes d884e8ab7aa69477c1af5d29cef24589efaf2b8e.
- **FIX**: Fix console noise on global disable #397.

## 2.23.1

- **FIX**: Rule position - zero is a valid position #387.
- **FIX**: Protect against race condition due to Sublime bug #390.

## 2.23.0

- **NEW**: Add links in menu to documentation and issues.
- **NEW**: Provide new local quickstart guide from the menu.
- **NEW**: Breaking change to `bh_tag.sublime-settings`. `tag_mode` is now an ordered list of dictionaries.  
`self_closing_patterns` and `single_tag_patterns` and replaced with `optional_tag_patterns`,  
`void_tag_patterns`, and `self_closing_tag_patterns`.
- **NEW**: Add new `first_line` rule for determining tag mode.
- **NEW**: New XML tag mode and better XHTML mode.
- **NEW**: Better special tag logic which handles optional tags, void tags, and self closing tags better. #384

## 2.22.1

- **FIX**: Fix changelog links

## 2.22.0

- **NEW**: Manual command to show offscreen bracket popup.  Can be invoked when cursor is anywhere between target  
bracket #378.
- **NEW**: When selecting the "Match brackets without threshold" link on the unmatched bracket popup, reshow the  
offscreen popup.
- **NEW**: Add support for "SINUMERIK840D" language #379.

## 2.21.6

- **FIX**: Fix PHP conditional #366.
- **FIX**: No line wrapping in code snippets in popups.

## 2.21.5

- **FIX**: Fix a break caused by 2.21.4 #364.
- **FIX**: Fix CSS in changelog

## 2.21.4

- **FIX**: Changelog command now works for older ST3 versions.

## 2.21.3

- **FIX**: Don't fail if mdpopups was not installed on old Sublime version.

## 2.21.2

- **FIX**: Fix changelog typo :).

## 2.21.1

- **NEW**: Message to not freak people out :).

## 2.21.0

- **NEW**: Require mdpopups 1.9.0.
- **NEW**: New changelog command.
- **NEW**: Add support for new LaTeX syntax.
