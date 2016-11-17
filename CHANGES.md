# BracketHighlighter 2.23.0
> Released Nov 16, 2016

- **NEW**: Add links in menu to documentation and issues.
- **NEW**: Provide new local quickstart guide from the menu.
- **NEW**: Breaking change to `bh_tag.sublime-settings`. `tag_mode` is now an ordered list of dictionaries.  
`self_closing_patterns` and `single_tag_patterns` and replaced with `optional_tag_patterns`,  
`void_tag_patterns`, and `self_closing_tag_patterns`.
- **NEW**: Add new `first_line` rule for determining tag mode.
- **NEW**: New XML tag mode and better XHTML mode.
- **NEW**: Better special tag logic which handles optional tags, void tags, and self closing tags better. [#384](https://github.com/facelessuser/BracketHighlighter/issues/384)

# BracketHighlighter 2.22.1
> Released Nov 5, 2016

- **FIX**: Fix changelog links

# BracketHighlighter 2.22.0
> Released Oct 30, 2016

- **NEW**: Manual command to show offscreen bracket popup.  Can be invoked when cursor is anywhere between target  
bracket [#378](https://github.com/facelessuser/BracketHighlighter/issues/378)
- **NEW**: When selecting the "Match brackets without threshold" link on the unmatched bracket popup, reshow the  
offscreen popup.
- **NEW**: Add support for "SINUMERIK840D" language [#379](https://github.com/facelessuser/BracketHighlighter/pull/379).

# BracketHighlighter 2.21.6
> Released Oct 19, 2016

- **FIX**: Fix PHP conditional [#366](https://github.com/facelessuser/BracketHighlighter/issues/366)
- **FIX**: No line wrapping in code snippets in popups.

# BracketHighlighter 2.21.5
> Released Aug 21, 2016

- **FIX**: Fix a break caused by 2.21.4 [#364](https://github.com/facelessuser/BracketHighlighter/issues/364)
- **FIX**: Fix CSS in changelog

# BracketHighlighter 2.21.4
> Released Aug 21, 2016

- **FIX**: Changelog command now works for older ST3 versions.

# BracketHighlighter 2.21.3
> Released Aug 1, 2016

- **FIX**: Don't fail if mdpopups was not installed on old Sublime version.

# BracketHighlighter 2.21.2
> Released Aug 1, 2016

- **FIX**: Fix changelog typo :).

# BracketHighlighter 2.21.1
> Released Aug 1, 2016

- **NEW**: Message to not freak people out :).

# BracketHighlighter 2.21.0
> Released Jul 31, 2016

- **NEW**: Require mdpopups 1.9.0.
- **NEW**: New changelog command.
- **NEW**: Add support for new LaTeX syntax.
