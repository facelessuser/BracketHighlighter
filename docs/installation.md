# Installation {: .doctitle}
Installing BracketHighlighter.

---

## Package Control
The recommended way to install BracketHighlighter is via [Package Control](https://packagecontrol.io/).  Package Control will install the correct branch on your system and keep it up to date.

1. Ensure Package Control is installed.  Instructions are found [here](https://packagecontrol.io/installation).

2. In Sublime Text, press <kbd>ctrl</kbd> + <kbd>shift</kbd> + <kbd>p</kbd> (Win, Linux) or <kbd>cmd</kbd> + <kbd>shift</kbd> + <kbd>p</kbd> (OSX) to bring up the quick panel and start typing `Package Control: Install Package`.  Select the command and it will show a list of installable plugins.

3. Start typing `BracketHighlighter`; when you see it, select it.

4. Restart to be sure everything is loaded proper.

5. Enjoy!

## Git Cloning

!!! warning "Warning"
    This is not the recommended way to install BracketHighlighter for the casual user as it requires the user to know which branch to install, know how to use git, and **will not** get automatically updated.

    If you are forking for a pull request, this is the way to go, just replace the official repository with the link for your fork.

1. Quit Sublime Text.

2. Open a terminal:

    ```
    cd /path/to/Sublime Text 3/Packages
    git clone https://github.com/facelessuser/BracketHighlighter.git BracketHighlighter
    ```

3. Restart Sublime Text.
