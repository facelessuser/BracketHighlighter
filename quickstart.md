# Getting Started

![screenshot](res://Packages/BracketHighlighter/docs/images/Example1.png){: width=769, height=270}

BracketHighlighter is designed to auto highlight your brackets in various source files.  In general, if you are using  
one of the common languages, BracketHighlighter will work out of the box.

It is advised that you disable Sublime's default bracket and tag matcher in your `Preferences.sublime-settings` file  
or you will have matching conflicts:

```js
    "match_brackets": false,
    "match_brackets_angle": false,
    "match_brackets_braces": false,
    "match_brackets_content": false,
    "match_brackets_square": false,
    "match_tags": false
```

BracketHighlighter also contains a number  
of extensions that allows for deleting, replacing, or even wrapping brackets; check out the [documentation](http://facelessuser.github.io/BracketHighlighter/usage/) to learn  
more about basic usage.

BracketHighlighter (if you are on the latest version of Sublime Text 3) also will show a popup on screen if you mouse  
over a bracket and the other matching pair is offscreen.  The popup will show the offscreen bracket with surrounding  
lines and allow you to jump to the offscreen bracket.

![popup](res://Packages/BracketHighlighter/docs/images/popup1.png){: width=300, height=179}

# Where It Doesn't Work

BracketHighlighter excludes plain text by default. The free form nature of plain text and lack of syntax highlight  
scoping makes it more difficult to detect intended brackets.

Some language might not be supported yet, but they can be added via pull requests.  Check out the [documentation](http://facelessuser.github.io/BracketHighlighter/customize/#configuring-brackets) to  
learn about adding bracket rules and take a look at the default [settings file](sub://Packages/BracketHighlighter/bh_core.sublime-settings) to see examples.

# My Language Isn't Supported

BracketHighlighter supports numerous different languages and specialty bracket types, but your language might not be 
supported yet. The most common requested enhancement for BracketHighlighter is for new rules to support for a new a
previously unsupported language. I, like you, am proficient in very specific languages. I probably don’t use your  
favorite language or there would already be a support for it. I don’t have time to learn the nuances of your language.  
For these reasons, support for new language brackets requires pull requests from the community.

Though I will not personally implement rules for your favorite language, I am more than willing to offer suggestions  
and guidance to help those who may struggle to create rules for their specific language of interest.

If you find a bug in a supported language I am familiar with, I am happy to address the issue.  If the bug is found in  
a language I am not proficient in, it is likely I will defer fixes to the community.  I may offer suggestions and  
encourage the issue creator to do the actual testing as they will be more familiar with the language.

# Customizing

BracketHighlighter can be tweaked to show specific brackets with specific colors and styles. Due to the way sublime  
handles colored regions, the method of specifying specific colors can be cumbersome, but it is all [documented](http://facelessuser.github.io/BracketHighlighter/customize/#configuring-highlight-style).

# Sometimes I See a Question Mark

BracketHighlighter's auto highlighting does not scan the entire file all at once, but it scans a small window for  
performance reasons.  If you see a question mark, it may be simply that the search threshold has been reached.  You  
can run a bracket match with no threshold from the command palette or the offscreen bracket popup dialog (if using  
the latest version of Sublime Text 3).  If you are dissatisfied with the default small threshold, it can be increased  
in the settings file.  Be mindful that extremely large thresholds may affect performance.  I personally use a value of  
`10000`.

![unmatched](res://Packages/BracketHighlighter/docs/images/unmatched_popup.png){: width=486, height=210}

# I Need Help!

That's okay.  Bugs are sometimes introduced or discovered in existing code.  Sometimes the documentation isn't clear.  
Support can be found over on the [official repo](https://github.com/facelessuser/BracketHighlighter/issues).  Make sure to first search the documentation and previous issues  
before opening a new issue.  And when creating a new issue, make sure to fill in the provided issue template.  Please  
be courteous and kind in your interactions.
