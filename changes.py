"""Changelog."""
import sublime
import sublime_plugin
import webbrowser

CSS = '''
html { {{'.background'|css}} }
div.bracket-highlighter { padding: 0; margin: 0; {{'.background'|css}} }
.bracket-highlighter h1, .bracket-highlighter h2, .bracket-highlighter h3,
.bracket-highlighter h4, .bracket-highlighter h5, .bracket-highlighter h6 {
    {{'.string'|css}}
}
.bracket-highlighter blockquote { {{'.comment'|css}} }
.bracket-highlighter a { text-decoration: none; }
'''


class BracketHighlighterChangesCommand(sublime_plugin.WindowCommand):
    """Changelog command."""

    def run(self):
        """Show the changelog in a new view."""
        try:
            import mdpopups
            has_phantom_support = (mdpopups.version() >= (1, 10, 0)) and (int(sublime.version()) >= 3118)
        except Exception:
            has_phantom_support = False

        text = sublime.load_resource('Packages/BracketHighlighter/CHANGES.md')
        view = self.window.new_file()
        view.set_name('BracketHighlighter - Changelog')
        view.settings().set('gutter', False)
        if has_phantom_support:
            mdpopups.add_phantom(
                view,
                'changelog',
                sublime.Region(0),
                text,
                sublime.LAYOUT_INLINE,
                wrapper_class="bracket-highlighter",
                css=CSS
            )
        else:
            view.run_command('insert', {"characters": text})
        view.set_read_only(True)
        view.set_scratch(True)

    def on_navigate(self, href):
        """Open links."""
        webbrowser.open_new_tab(href)
