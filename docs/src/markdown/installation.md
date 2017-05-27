# Installation

## Package Control
The recommended way to install BracketHighlighter is via [Package Control][package-control].  Package Control will install the correct branch on your system and keep it up to date.

---

1. Ensure Package Control is installed.  Instructions are found [here][package-control-install].

2. In Sublime Text, press ++ctrl+shift+p++ (Win, Linux) or ++cmd+shift+p++ (OSX) to bring up the quick panel and start typing `Package Control: Install Package`.  Select the command and it will show a list of installable plugins.

3. Start typing `BracketHighlighter`; when you see it, select it.

4. Restart to be sure everything is loaded proper.

5. Enjoy!

## Manual Installation

!!! warning "Warning"
    This is not the recommended way to install BracketHighlighter for the average user.  Installing this way **will not** get automatically updated.

    If you are forking for a pull request, you should **just** clone BH and run Package Control's `Satisfy Dependency` command to get all the dependencies.

For those who want to install BH without package control, here are the steps.  It is understood that some people, for what ever reason, will prefer manual install and may even have legitimate reasons to do so.  When going this route, you will have to keep all the packages updated yourself.

---

1. Download the latest releases of the following dependencies and unpack or git clone in the `Packages` folder as shown below:

    - https://bitbucket.org/teddy_beer_maniac/sublime-text-dependency-markupsafe -> `markupsafe`
    - https://bitbucket.org/teddy_beer_maniac/sublime-text-dependency-jinja2 -> `python-jinja2`
    - https://github.com/packagecontrol/pygments -> `pygments`
    - https://github.com/facelessuser/sublime-markdown-popups -> `mdpopups`
    - https://github.com/facelessuser/sublime-markdown -> `python-markdown`
    - https://github.com/facelessuser/sublime-backrefs -> `backrefs`

2. Download and unpack, or git clone, the latest BracketHighlighter release and unpack as `BracketHighlighter`:

    - https://github.com/facelessuser/BracketHighlighter -> BracketHighlighter

3. Create a folder under `Packages` called `00-dependencies` and under that folder create a file called `00-dependencies.py`:

    Copy the following code to `00-dependencies.py` (this code was taken from Package Control):

    ``` python
    import sys
    import os
    from os.path import dirname

    if os.name == 'nt':
        from ctypes import windll, create_unicode_buffer

    import sublime


    if sys.version_info >= (3,):
        def decode(path):
            return path

        def encode(path):
            return path

        if os.path.basename(__file__) == 'sys_path.py':
            pc_package_path = dirname(dirname(__file__))
        # When loaded as a .sublime-package file, the filename ends up being
        # Package Control.sublime-package/Package Control.package_control.sys_path
        else:
            pc_package_path = dirname(__file__)
        st_version = u'3'

    else:
        def decode(path):
            if not isinstance(path, unicode):
                path = path.decode(sys.getfilesystemencoding())
            return path

        def encode(path):
            if isinstance(path, unicode):
                path = path.encode(sys.getfilesystemencoding())
            return path

        pc_package_path = decode(os.getcwd())
        st_version = u'2'


    st_dir = dirname(dirname(pc_package_path))


    def add(path, first=False):
        """
        Adds an entry to the beginning of sys.path, working around the fact that
        Python 2.6 can't import from non-ASCII paths on Windows.

        :param path:
            A unicode string of a folder, zip file or sublime-package file to
            add to the path

        :param first:
            If the path should be added at the beginning
        """

        if os.name == 'nt':
            # Work around unicode path import issue on Windows with Python 2.6
            buf = create_unicode_buffer(512)
            if windll.kernel32.GetShortPathNameW(path, buf, len(buf)):
                path = buf.value

        enc_path = encode(path)

        if os.path.exists(enc_path):
            if first:
                try:
                    sys.path.remove(enc_path)
                except (ValueError):
                    pass
                sys.path.insert(0, enc_path)
            elif enc_path not in sys.path:
                sys.path.append(enc_path)


    def remove(path):
        """
        Removes a path from sys.path if it is present

        :param path:
            A unicode string of a folder, zip file or sublime-package file
        """

        try:
            sys.path.remove(encode(path))
        except (ValueError):
            pass

        if os.name == 'nt':
            buf = create_unicode_buffer(512)
            if windll.kernel32.GetShortPathNameW(path, buf, len(buf)):
                path = buf.value
            try:
                sys.path.remove(encode(path))
            except (ValueError):
                pass


    def generate_dependency_paths(name):
        """
        Accepts a dependency name and generates a dict containing the three standard
        import paths that are valid for the current machine.

        :param name:
            A unicode string name of the dependency

        :return:
            A dict with the following keys:
             - 'ver'
             - 'plat'
             - 'arch'
        """

        packages_dir = os.path.join(st_dir, u'Packages')
        dependency_dir = os.path.join(packages_dir, name)

        ver = u'st%s' % st_version
        plat = sublime.platform()
        arch = sublime.arch()

        return {
            'all': os.path.join(dependency_dir, 'all'),
            'ver': os.path.join(dependency_dir, ver),
            'plat': os.path.join(dependency_dir, u'%s_%s' % (ver, plat)),
            'arch': os.path.join(dependency_dir, u'%s_%s_%s' % (ver, plat, arch))
        }


    def add_dependency(name, first=False):
        """
        Accepts a dependency name and automatically adds the appropriate path
        to sys.path, if the dependency has a path for the current platform and
        architecture.

        :param name:
            A unicode string name of the dependency

        :param first:
            If the path should be added to the beginning of the list
        """

        dep_paths = generate_dependency_paths(name)

        for path in dep_paths.values():
            if os.path.exists(encode(path)):
                add(path, first=first)


    add_dependency('pygments')
    add_dependency('backrefs')
    add_dependency('markupsafe')
    add_dependency('python-markdown')
    add_dependency('python-jinja2')
    add_dependency('mdpopups')

    ```

4. Restart and enjoy.


## Git Cloning

1. Quit Sublime Text.

2. Open a terminal and enter the following.  For dependencies, replace the URL with the appropriate URL, and the appropriate folder to check it out to:

    ```
    cd /path/to/Sublime Text 3/Packages
    git clone https://github.com/facelessuser/BracketHighlighter.git BracketHighlighter
    ```

3. Restart Sublime Text.

--8<-- "refs.md"
