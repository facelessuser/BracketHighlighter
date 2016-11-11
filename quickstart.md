# Getting Started

BracketHighlighter is designed to auto highlight your brackets in various source files.  In general, if you are using one of the common languages, BracketHighlighter will work out of the box.  BracketHighlighter also contains a number of extensions that allow for deleting, replacing, or even wrapping brackets; check out the [documentation](http://facelessuser.github.io/BracketHighlighter/usage/) to learn more about basic usage.

BracketHighlighter (if you are on the latest version of Sublime Text 3) also will show a popup on screen if you mouse over a bracket and the other matching pair is offscreen.  The popup will show the offscreen bracket with surrounding lines and allow you to jump to the offscreen bracket.

# Where It Doesn't Work

BracketHighlighter excludes plain text by default due to the free form nature and lack of syntax highlight scoping in plain text makes it more difficult to detect intended brackets.

Some language might not be supported yet, but they can be added via pull requests.  Check out the [documentation](http://facelessuser.github.io/BracketHighlighter/customize/#configuring-brackets) to learn about adding bracket rules and take a look at the default [settings file](sub://Packages/BracketHighlighter/bh_core.sublime-settings) to see examples.

# Customizing

BracketHighlighter can be tweaked to show specific brackets with specific colors and styles. Due to the way sublime handles colored regions, the method of specifying specific colors can be cumbersome, but it is all [documented](http://facelessuser.github.io/BracketHighlighter/customize/#configuring-highlight-style).

# Sometimes I See a Question Mark

BracketHighlighter's auto highlighting does not scan the entire file all at once, but it scans a small window for performance reasons.  If you see a question mark, it may be simply that the search threshold has been reached.  You can run a bracket match with no threshold from the command palette or the offscreen bracket popup dialog (if using the latest version of Sublime Text 3).

# I Need Help!

That's okay.  Bugs are sometimes introduced or discovered in existing code.  Sometimes the documentation isn't clear.  Support can be found over on the [official repo](https://github.com/facelessuser/BracketHighlighter/issues).  Make sure to first search the documentation and previous issues before opening a new issue.  And when creating a new issue, make sure to fill in the provided issue template.  Please be courteous and kind in your interactions.
