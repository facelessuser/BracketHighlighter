import sublime
import sublime_plugin
import mdpopups
import backrefs
import textwrap

__version__ = (2, 19, 0)
__pc_name__ = 'BracketHighlighter'


def list2string(obj):
    """Convert list to string."""

    return '.'.join([str(x) for x in obj])


def format_version(module, attr, call=False):
    """Format the version."""

    try:
        if call:
            version = getattr(module, attr)()
        else:
            version = getattr(module, attr)
    except Exception as e:
        print(e)
        version = 'Version could not be acquired!'

    if not isinstance(version, str):
        version = list2string(version)
    return version


def is_installed_by_package_control():
    """Check if installed by package control."""

    settings = sublime.load_settings('Package Control.sublime-settings')
    return str(__pc_name__ in set(settings.get('installed_packages', [])))


class BhSupportInfoCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        info = {
            "platform": sublime.platform(),
            "version": sublime.version(),
            "arch": sublime.arch(),
            "bh_version": list2string(__version__),
            "mdpopups_version": format_version(mdpopups, 'version', call=True),
            "backrefs_version": format_version(backrefs, 'version'),
            "pc_install": is_installed_by_package_control()
        }

        msg = textwrap.dedent(
            """\
            - ST ver.:        %(version)s
            - Platform:       %(platform)s
            - Arch:           %(arch)s
            - Plugin ver.:    %(bh_version)s
            - Install via PC: %(pc_install)s
            - Mdpopups ver.:  %(mdpopups_version)s
            - Backrefs ver.:  %(backrefs_version)s
            """ % info
        )

        sublime.message_dialog(msg + '\nInfo has been copied to the clipboard.')
        sublime.set_clipboard(msg)
