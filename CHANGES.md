# BracketHighlighter 2.27.0

Nov 19, 2017

- **NEW**: Add option to always show the bracket popup on bracket hover [#457](https://github.com/facelessuser/BracketHighlighter/pull/457).
- **FIX**: Fix clone views not properly supported [#454](https://github.com/facelessuser/BracketHighlighter/issues/454).
- **FIX**: Improvements to Ruby conditional matching [#452](https://github.com/facelessuser/BracketHighlighter/issues/452).

# BracketHighlighter 2.26.0

Nov 5, 2017

- **NEW**: Added new configuration `user_bracket_styles` to allow a user to override specific rules or just part of a  
specific rule instead of copying all of `bracket_styles` [#448](https://github.com/facelessuser/BracketHighlighter/pull/448).
- **NEW**: Add colorization with region-ish scopes for Sublime builds 3148+ [#448](https://github.com/facelessuser/BracketHighlighter/pull/448).
- **FIX**: Ruby issue with conditionals immediately followed after return keyword [#425](https://github.com/facelessuser/BracketHighlighter/issues/425).
- **FIX**: PHP issue for arrows (`$var->prop`) [#446](https://github.com/facelessuser/BracketHighlighter/pull/446).

# BracketHighlighter 2.25.2

Oct 24, 2017

- **FIX**: Update tag attribute pattern.
- **FIX**: Add SVG self closing tags.
- **FIX**: Temporarily use `thin_underline` style to mitigate issue [#443](https://github.com/facelessuser/BracketHighlighter/issues/443).

# BracketHighlighter 2.25.1

Oct 8, 2017

- **FIX**: Update dependencies.

# BracketHighlighter 2.25.0

Aug 12, 2017

- **FIX**: Quick start image links.
- **FIX**: Allow Markdown related brackets to work in Markdown Extended.
- **FIX**: Allow `HTML (Jinja2)` to work in HTML.
- **NEW**: Add Markdown `` ` `` to swap and wrap.
- **NEW**: Add commonly used commands to the command panel (documents and settings) [#419](https://github.com/facelessuser/BracketHighlighter/issues/419).

# BracketHighlighter 2.24.2

June 15, 2017

- **FIX**: Avoid things like `->` in PHP due to new Sublime default syntax changes [#417](https://github.com/facelessuser/BracketHighlighter/issues/417).
- **FIX**: Add support for Python f-strings.

# BracketHighlighter 2.24.1

May 26, 2017

- **FIX**: Random regions failure.
- **FIX**: Lua keyword match at beginning of line.

# BracketHighlighter 2.24.0

May 10, 2017

- **NEW**: Popup/Phantom support limited to 3124+ moving forward to prepare for `mdpopups` 2.0 that will drop legacy  
support for old, early implementation of popups and phantoms.
- **NEW**: No longer try and force dependency updates.  Leave it up to Package Control (whether they do it or not).
- **NEW**: CSS adjustments to popups.
- **FIX**: Fix tag matching corner case [#409](https://github.com/facelessuser/BracketHighlighter/issues/409).

# BracketHighlighter 2.23.3

Jan 24, 2017

- **FIX**: Fix error `ImportError: No module named 'yaml'` [#400](https://github.com/facelessuser/BracketHighlighter/issues/400).

# BracketHighlighter 2.23.2

Jan 23, 2017

- **FIX**: Add backtick quote support for ruby and shell script syntaxes [d884e8a](https://github.com/facelessuser/BracketHighlighter/commit/d884e8ab7aa69477c1af5d29cef24589efaf2b8e).
- **FIX**: Fix console noise on global disable [#397](https://github.com/facelessuser/BracketHighlighter/issues/397).

# BracketHighlighter 2.23.1

Nov 25, 2016

- **FIX**: Rule position - zero is a valid position [#387](https://github.com/facelessuser/BracketHighlighter/issues/387).
- **FIX**: Protect against race condition due to Sublime bug [#390](https://github.com/facelessuser/BracketHighlighter/issues/390).

# BracketHighlighter 2.23.0

Nov 16, 2016

- **NEW**: Add links in menu to documentation and issues.
- **NEW**: Provide new local quickstart guide from the menu.
- **NEW**: Breaking change to `bh_tag.sublime-settings`. `tag_mode` is now an ordered list of dictionaries.  
`self_closing_patterns` and `single_tag_patterns` and replaced with `optional_tag_patterns`,  
`void_tag_patterns`, and `self_closing_tag_patterns`.
- **NEW**: Add new `first_line` rule for determining tag mode.
- **NEW**: New XML tag mode and better XHTML mode.
- **NEW**: Better special tag logic which handles optional tags, void tags, and self closing tags better. [#384](https://github.com/facelessuser/BracketHighlighter/issues/384)

# BracketHighlighter 2.22.1

Nov 5, 2016

- **FIX**: Fix changelog links

# BracketHighlighter 2.22.0

Oct 30, 2016

- **NEW**: Manual command to show offscreen bracket popup.  Can be invoked when cursor is anywhere between target  
bracket [#378](https://github.com/facelessuser/BracketHighlighter/issues/378)
- **NEW**: When selecting the "Match brackets without threshold" link on the unmatched bracket popup, reshow the  
offscreen popup.
- **NEW**: Add support for "SINUMERIK840D" language [#379](https://github.com/facelessuser/BracketHighlighter/pull/379).

# BracketHighlighter 2.21.6

Oct 19, 2016

- **FIX**: Fix PHP conditional [#366](https://github.com/facelessuser/BracketHighlighter/issues/366)
- **FIX**: No line wrapping in code snippets in popups.

# BracketHighlighter 2.21.5

Aug 21, 2016

- **FIX**: Fix a break caused by 2.21.4 [#364](https://github.com/facelessuser/BracketHighlighter/issues/364)
- **FIX**: Fix CSS in changelog

# BracketHighlighter 2.21.4

Aug 21, 2016

- **FIX**: Changelog command now works for older ST3 versions.

# BracketHighlighter 2.21.3

Aug 1, 2016

- **FIX**: Don't fail if mdpopups was not installed on old Sublime version.

# BracketHighlighter 2.21.2

Aug 1, 2016

- **FIX**: Fix changelog typo :).

# BracketHighlighter 2.21.1

Aug 1, 2016

- **NEW**: Message to not freak people out :).

# BracketHighlighter 2.21.0

Jul 31, 2016

- **NEW**: Require mdpopups 1.9.0.
- **NEW**: New changelog command.
- **NEW**: Add support for new LaTeX syntax.
