import sublime


def log(msg):
    print "BracketHighlighter: %s" % msg


def debug(msg):
    if sublime.load_settings("bh_core.sublime-settings").get('debug_enable', False):
        log(msg)
