"""
BracketHighlighter.

Copyright (c) 2013 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT

Handles popups.
"""
import sublime
import re
import textwrap
import traceback
from .bh_logging import log

HOVER_SUPPORT = int(sublime.version()) >= 3124
WRAPPER_CLASS = "bracket-highlighter"

CSS = '''
{%- if var.mdpopups_version >= (2, 0, 0) %}
div.bracket-highlighter { padding: 0.5rem; margin: 0; }
{%- else %}
div.bracket-highlighter { padding: 0; margin: 0; }
{%- endif %}
'''
MATCH_ERR = '''
\x02{%%- if plugin.mdpopups_version >= (2, 0, 0) %%}\x03
!!! panel-error "Matching bracket could not be found!"

    - There *might* be no match.
    - Brackets *might* be nested poorly --> `([)(])`
    - Matching bracket *might* be beyond the search threshold.
    A match done without the threshold *might* find it.

[(Match brackets without threshold)](%(pt)s)
\x02{%%- else %%}\x03
### Matching bracket could not be found! {: .error}

- There *might* be no match.
- Brackets *might* be nested poorly --> `([)(])`
- Matching bracket *might* be beyond the search threshold.
A match done without the threshold *might* find it.
[(Match brackets without threshold)](%(pt)s)
\x02{%%- endif %%}\x03
'''

template_options = {
    "block_start_string": "\x02{%",
    "block_end_string": "%}\x03",
    "variable_start_string": "\x02{{",
    "variable_end_string": "}}\x03",
    "comment_start_string": "\x02{#",
    "comment_end_string": "#}\x03"
}

if HOVER_SUPPORT:
    import mdpopups


class BhOffscreenPopup(object):
    """Handle offscreen popups."""

    popup_view = None

    def on_navigate(self, href):
        """Navigate to code position."""
        if HOVER_SUPPORT:
            try:
                pt = int(href)
                self.popup_view.sel().clear()
                self.popup_view.sel().add(sublime.Region(pt))
                self.popup_view.show(pt)
                mdpopups.hide_popup(self.popup_view)
            except Exception:
                log("Problem handling popup event:\n%s" % str(traceback.format_exc()))

    def on_navigate_unmatched(self, href):
        """Handle unmatched click."""
        if HOVER_SUPPORT:
            pt = int(href)
            mdpopups.hide_popup(self.popup_view)
            self.popup_view.run_command("bh_offscreen_popup", {"point": pt, "no_threshold": True})

    def show_unmatched_popup(self, view, point):
        """Show unmatched popup."""

        if HOVER_SUPPORT:
            self.popup_view = view
            mdpopups.show_popup(
                view,
                textwrap.dedent(MATCH_ERR % {"pt": str(point)}),
                wrapper_class=WRAPPER_CLASS,
                flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                css=CSS,
                max_width=800,
                max_height=800,
                location=point,
                on_navigate=self.on_navigate_unmatched,
                template_vars={'mdpopups_version': mdpopups.version()},
                template_env_options=template_options
            )

    def is_bracket_visible(self, view, region):
        """
        Check if bracket is visible.

        Check if first point of bracket is visible or last point is visible.
        In short, is any part visible?

        ```
        (xa,ya)--------------------(xb,ya)
        |                             |
        |                             |
        |    (pxa,pya){(pxb,pyb)      |
        |                             |
        |                             |
        (xa,yb)------------------------
        ```
        """

        # Always report that bracket is not visible if we always want to show the popup
        if sublime.load_settings("bh_core.sublime-settings").get('show_bracket_popup_always', False):
            return False

        xa, ya = view.viewport_position()
        w, h = view.viewport_extent()
        xb, yb = xa + w, ya + h
        pxa, pya = view.text_to_layout(region[0])
        pxb, pyb = view.text_to_layout(region[1])

        return (xa <= pxa < xb and ya <= pya < yb) or (xa <= pxb < xb and ya <= pyb < yb)

    def get_context_line(self, view, row, col_start, col_end, tab_size):
        """Get line context."""

        line = view.line(view.text_point(row, 0))
        c0 = view.rowcol(line.begin())[1]
        c1 = view.rowcol(line.end())[1]
        if c0 < col_start:
            c0 = col_start
        if c0 > c1:
            c0 = c1
        diff = c1 - c0
        if diff > 120:
            c1 -= diff - 120

        return self.escape_code(
            view.substr(
                sublime.Region(
                    view.text_point(row, c0),
                    view.text_point(row, c1)
                )
            ),
            tab_size
        )

    def get_multiline_context(self, view, code, row, col_start, col_end, tab_size, line_context):
        """Get multi-line context for vertical offscreen brackets."""

        last_row = view.rowcol(view.size())[0]

        lines = [code]

        offset = 1
        while offset <= line_context:
            current_row = row - offset
            if current_row >= 0:
                lines.insert(0, self.get_context_line(view, current_row, col_start, col_end, tab_size))
            else:
                break
            offset += 1
        last_offset = offset

        offset = 1
        while offset <= line_context or (len(lines) != (line_context * 2) + 1):
            current_row = row + offset
            if current_row <= last_row:
                lines.append(self.get_context_line(view, current_row, col_start, col_end, tab_size))
            else:
                break
            offset += 1

        offset = last_offset
        while len(lines) < ((line_context * 2) + 1):
            current_row = row - offset
            if current_row >= 0:
                lines.insert(0, self.get_context_line(view, current_row, col_start, col_end, tab_size))
            else:
                break
            offset += 1

        return textwrap.dedent('\n'.join(lines)).replace('\n', '<br>')

    def escape_code(self, text, tab_size):
        """Format text to HTML."""

        encode_table = {
            '&': '&amp;',
            '>': '&gt;',
            '<': '&lt;',
            '\t': ' ' * tab_size,
            '\n': '',
            ' ': '&nbsp;'
        }

        return ''.join(
            encode_table.get(c, c) for c in text
        )

    def show_popup_between(self, view, point, region, region2, icon):
        """Show popup between."""
        if HOVER_SUPPORT:
            markup = ''
            if not self.is_bracket_visible(view, region):
                markup += self.get_markup(view, point, region, icon)
            if not self.is_bracket_visible(view, region2):
                markup += '\n\n'
                markup += self.get_markup(view, point, region2, icon)
            if markup:
                self.popup_view = view
                mdpopups.show_popup(
                    view,
                    markup,
                    wrapper_class=WRAPPER_CLASS,
                    css=CSS,
                    flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                    max_width=800,
                    location=point,
                    on_navigate=self.on_navigate,
                    template_vars={'mdpopups_version': mdpopups.version()},
                    template_env_options=template_options
                )
            else:
                self.show_unmatched_popup(view, point)

    def get_markup(self, view, point, region, icon):
        """Get markup."""

        settings = sublime.load_settings('bh_core.sublime-settings')
        tab_size = view.settings().get('tab_size', 4)

        # Get highlight colors
        color = None
        if icon is not None:
            color = mdpopups.scope2style(view, icon[1]).get('color')
        if color is None or bool(settings.get('use_custom_popup_bracket_emphasis', False)):
            bracket_em = settings.get('popup_bracket_emphasis', '#ff0000')
            if not bracket_em.startswith('#'):
                bracket_em = mdpopups.scope2style(view, bracket_em).get('color')
        else:
            bracket_em = color

        # Get positions of bracket extents on the line
        row, col = view.rowcol(region[0])
        col2 = view.rowcol(region[1])[1]

        # Calculate how far before and after bracket we can/should grab for context
        # Format and truncate (if necessary).
        context = int(settings.get('popup_char_context', 120)) - (col2 - col) - 1
        start = region[1] - context
        col_start = col2 - context
        overage = 0
        line = view.line(region[0])
        if start < line.begin():
            overage = line.begin() - start
            start = line.begin()
            col_start = 0
        end = region[1] + overage
        col_end = col2 + overage
        if end > line.end():
            end = line.end()
            col_end = view.rowcol(line.end())[1]

        # Get line of code with bracket and emphasize the bracket
        content = view.substr(sublime.Region(start, end))
        if re.match(r'#([\da-fA-F]{3}){1,2}', bracket_em):
            highlight_open = '<span class="brackethighlighter" style="color: %s;"><strong>' % bracket_em
        else:
            highlight_open = '<span class="brackethighlighter %s"><strong>' % bracket_em
        content = (
            self.escape_code(content[:col - col_start], tab_size) +
            highlight_open +
            self.escape_code(content[col - col_start: col2 - col_start], tab_size) +
            '</strong></span>' +
            self.escape_code(content[col2 - col_start:], tab_size)
        )

        # Get additional lines of context (if required) and format text
        if row != view.rowcol(point)[0]:
            line_context = int(int(settings.get('popup_line_context', 2)) / 2)
            content = self.get_multiline_context(view, content, row, col_start, col_end, tab_size, line_context)
        else:
            content = content.strip()

        # Put together the markup to show
        markup = '<div class="highlight"><pre>%s</pre></div>\n' % content
        markup += '\n' + '[(jump to bracket - line: %d)](%d)' % (row + 1, region[0])

        return markup

    def show_popup(self, view, point, region, icon):
        """Show the popup."""

        if HOVER_SUPPORT:
            if not self.is_bracket_visible(view, region):
                markup = self.get_markup(view, point, region, icon)

                self.popup_view = view
                mdpopups.show_popup(
                    view,
                    markup,
                    wrapper_class=WRAPPER_CLASS,
                    css=CSS,
                    flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                    max_width=800,
                    location=point,
                    on_navigate=self.on_navigate,
                    template_vars={'mdpopups_version': mdpopups.version()},
                    template_env_options=template_options
                )
