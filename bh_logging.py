import sublime


def bh_log(msg):
    print("BracketHighlighter: %s" % msg)


def bh_debug(msg):
    if sublime.load_settings("bh_core.sublime-settings").get('debug_enable', False):
        bh_log(msg)
