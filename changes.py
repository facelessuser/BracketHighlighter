"""Changelog."""
import sublime
import sublime_plugin

CSS = '''
.bracket-highlighter h1, .bracket-highlighter h2, .bracket-highlighter h3,
.bracket-highlighter h4, .bracket-highlighter h5, .bracket-highlighter h6 {
    {{'.string'|css('color')}}
}
.bracket-highlighter blockquote { {{'.comment'|css('color')}} }
'''


class BhChangesCommand(sublime_plugin.WindowCommand):
    """Changelog command."""

    def run(self):
        """Show the changelog in a new view."""
        import mdpopups

        text = sublime.load_resource('Packages/BracketHighlighter/CHANGES.md')
        view = self.window.new_file()
        view.set_name('BracketHighlighter - Changelog')
        view.settings().set('gutter', False)
        html = '<div class="bracket-highlighter">%s</div>' % mdpopups.md2html(view, text)
        mdpopups.add_phantom(view, 'changelog', sublime.Region(0), html, sublime.LAYOUT_INLINE, css=CSS)
        view.set_read_only(True)
        view.set_scratch(True)

    def is_enabled(self):
        """Check if is enabled."""
        try:
            import mdpopups
        except Exception:
            return False

        return (mdpopups.version() >= (1, 7, 3)) and (int(sublime.version()) >= 3118)

    is_visible = is_enabled
