[![Donate via PayPal][donate-image]][donate-link]
[![Discord][discord-image]][discord-link]
[![Build][github-ci-image]][github-ci-link]
[![Package Control Downloads][pc-image]][pc-link]
![License][license-image]
# BracketHighlighter

Bracket Highlighter matches a variety of brackets such as: `[]`, `()`, `{}`, `""`, `''`, `<tag></tag>`, and even custom brackets.

This was originally forked from pyparadigm's _SublimeBrackets_ and _SublimeTagmatcher_ (both are no longer available).  I forked this to fix some issues I had and to add some features I had wanted.  I also wanted to improve the efficiency of the matching.

Moving forward, I have thrown away all of the code and have completely rewritten the entire code base to allow for a more flexibility, faster, and more feature rich experience.

![screenshot](docs/src/markdown/images/Example1.png)

# Feature List

- Customizable to highlight almost any bracket.
- Customizable bracket highlight style.
- High visibility bracket highlight mode.
- Selectively disable or enable specific matching of tags, brackets, or quotes.
- Selectively use an allowlist or blocklist for matching specific tags, brackets, or quotes based on language.
- When bound to a shortcut, allow option to show line count and char count between match in the status bar.
- Highlight basic brackets within strings.
- Works with multi-select.
- Configurable custom gutter icons.
- Toggle bracket escape mode for string brackets (regex|string).
- Bracket plugins that can jump between bracket ends, select content, remove brackets and/or content, wrap selections with brackets, swap brackets, swap quotes (handling quote escaping between the main quotes), fold/unfold content between brackets, toggle through tag attribute selection, select both the opening and closing tag name to change both simultaneously.

# Documentation

https://facelessuser.github.io/BracketHighlighter/

# License

Released under the MIT license.

Copyright (c) 2013 - 2020 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

[github-ci-image]: https://github.com/facelessuser/BracketHighlighter/workflows/build/badge.svg?branch=master&event=push
[github-ci-link]: https://github.com/facelessuser/BracketHighlighter/actions?query=workflow%3Abuild+branch%3Amaster
[discord-image]: https://img.shields.io/discord/678289859768745989?logo=discord&logoColor=aaaaaa&color=mediumpurple&labelColor=333333
[discord-link]: https://discord.gg/TWs8Tgr
[pc-image]: https://img.shields.io/packagecontrol/dt/BracketHighlighter.svg?labelColor=333333&logo=sublime%20text
[pc-link]: https://packagecontrol.io/packages/BracketHighlighter
[license-image]: https://img.shields.io/badge/license-MIT-blue.svg?labelColor=333333
[donate-image]: https://img.shields.io/badge/Donate-PayPal-3fabd1?logo=paypal
[donate-link]: https://www.paypal.me/facelessuser
