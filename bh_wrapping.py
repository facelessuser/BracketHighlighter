import sublime
import sublime_plugin
from os.path import basename
import re


BH_TABSTOPS = re.compile(r"(\$\{BH_(SEL|TAB)(?:\:([^\}]+))?\})")
TAB_REGION = "bh_plugin_wrapping_tabstop"
SEL_REGION = "bh_plugin_wrapping_select"
OUT_REGION = "bh_plugin_wrapping_outlier"

VALID_INSERT_STYLES = (
    ("inline", "Inline Insert"),
    ("block", "Block Insert"),
    ("indent_block", "Indented Block Insert")
)


def exclude_entry(enabled, filter_type, language_list, language):
    """
    Exclude bracket wrapping entry by filter
    """

    exclude = True
    if enabled:
        # Black list languages
        if filter_type == 'blacklist':
            exclude = False
            if language != None:
                for item in language_list:
                    if language == item.lower():
                        exclude = True
                        break
        #White list languages
        elif filter_type == 'whitelist':
            if language != None:
                for item in language_list:
                    if language == item.lower():
                        exclude = False
                        break
    return exclude


class TextInsertion(object):
    """
    Wrapper class for inserting text
    """

    def __init__(self, view, edit):
        """
        Store view and edit objects
        """

        self.view = view
        self.edit = edit

    def insert(self, pt, text):
        """
        Peform insertion
        """

        return self.view.insert(self.edit, pt, text)


class WrapBrackets(object):
    """
    Wrap the current selection(s) with the defined wrapping options
    """

    def __init__(self, view, setting_file, attribute):
        self.view = view
        self._menu = []
        self._brackets = []
        self._insert = []
        self._style = []
        self.read_wrap_entries(setting_file, attribute)

    def inline(self, edit, sel):
        """
        Inline wrap
        """

        ti = TextInsertion(self.view, edit)

        offset1 = ti.insert(sel.begin(), self.brackets[0])
        self.insert_regions.append(sublime.Region(sel.begin(), sel.begin() + offset1))
        offset2 = ti.insert(sel.end() + offset1, self.brackets[1])
        self.insert_regions.append(sublime.Region(sel.end() + offset1, sel.end() + offset1 + offset2))

    def block(self, edit, sel, indent=False):
        """
        Wrap brackets around selection and block off the content
        """

        # Calculate number of lines between brackets
        self.calculate_lines(sel)
        # Calculate the current indentation of first bracket
        self.calculate_indentation(sel)

        ti = TextInsertion(self.view, edit)

        line_offset = 0
        first_end = 0
        second_end = 0
        second_start = sel.end()

        for b in reversed(self.brackets[1].split('\n')):
            second_end += ti.insert(sel.end(), "\n" + self.indent_to_col + b)
        num_open_lines = self.brackets[0].count('\n')
        for b in reversed(self.brackets[0].split('\n')):
            if line_offset == num_open_lines:
                line = b + "\n"
            else:
                line = self.indent_to_col + b + "\n"
            first_end += ti.insert(sel.begin(), line)
            line_offset += 1
        self.insert_regions.append(sublime.Region(sel.begin(), sel.begin() + first_end))

        if indent:
            second_start += self.indent_content(ti, line_offset)
        else:
            pt = self.view.text_point(self.first_line + line_offset, 0)
            second_start += ti.insert(pt, self.indent_to_col)

        self.insert_regions.append(sublime.Region(first_end + second_start, first_end + second_start + second_end))

    def indent_content(self, ti, line_offset):
        """
        Indent the block content
        """

        first = True
        offset = 0
        for l in range(line_offset, self.total_lines + line_offset):
            pt = self.view.text_point(self.first_line + l, 0)
            if first:
                offset += ti.insert(pt, self.indent_to_col + "\t")
                first = False
            else:
                offset += ti.insert(pt, "\t")
        return offset

    def calculate_lines(self, sel):
        """
        Calculate lines between brackets
        """

        self.first_line, self.col_position = self.view.rowcol(sel.begin())
        last_line = self.view.rowcol(sel.end())[0]
        self.total_lines = last_line - self.first_line + 1

    def calculate_indentation(self, sel):
        """
        Calculate how much lines should be indented
        """

        tab_size = self.view.settings().get("tab_size", 4)
        tab_count = self.view.substr(sublime.Region(sel.begin() - self.col_position, sel.begin())).count('\t')
        spaces = self.col_position - tab_count
        self.indent_to_col = "\t" * tab_count + "\t" * (spaces / tab_size) + " " * (spaces % tab_size if spaces >= tab_size else spaces)

    def select(self, edit):
        """
        Select defined regions after wrapping
        """

        self.view.sel().clear()
        map(lambda x: self.view.sel().add(x), self.insert_regions)

        final_sel = []
        initial_sel = []
        for s in self.view.sel():
            string = self.view.substr(s)
            matches = [m for m in BH_TABSTOPS.finditer(string)]
            multi_offset = 0
            if matches:
                for m in matches:
                    r = sublime.Region(s.begin() + multi_offset + m.start(1), s.begin() + multi_offset + m.end(1))
                    if m.group(3):
                        replace = m.group(3)
                        self.view.erase(edit, r)
                        added = self.view.insert(edit, r.begin(), replace)
                        final_sel.append(sublime.Region(s.begin() + multi_offset + m.start(1), s.begin() + multi_offset + m.start(1) + added))
                        multi_offset += added - r.size()
                    else:
                        self.view.erase(edit, r)
                        final_sel.append(sublime.Region(s.begin() + multi_offset + m.start(1)))
                        multi_offset -= r.size()
                    if m.group(2) == "SEL":
                        initial_sel.append(final_sel[-1])

        if len(initial_sel) != len(final_sel):
            self.view.add_regions(TAB_REGION, final_sel, "", "", sublime.HIDDEN)

        # Re-position cursor
        self.view.sel().clear()
        if len(initial_sel):
            map(lambda x: self.view.sel().add(x), initial_sel)
        elif len(final_sel):
            self.view.sel().add(final_sel[0])

    def read_wrap_entries(self, setting_file, attribute):
        """
        Read wrap entries from the settings file
        """

        settings = sublime.load_settings(setting_file)
        syntax = self.view.settings().get('syntax')
        language = basename(syntax).replace('.tmLanguage', '').lower() if syntax != None else "plain text"
        wrapping = settings.get(attribute, [])
        for i in wrapping:
            if not exclude_entry(i["enabled"], i["language_filter"], i["language_list"], language):
                for j in i.get("entries", []):
                    try:
                        menu_entry = j["name"]
                        bracket_entry = j["brackets"]
                        insert_style = j.get("insert_style", ["inline"])
                        self._menu.append(menu_entry)
                        self._brackets.append(bracket_entry)
                        self._insert.append(insert_style)
                    except Exception:
                        pass

    def wrap_brackets(self, value):
        """
        Wrap selection(s) with defined brackets
        """

        if value < 0:
            return

        # Use new edit object since the main run has already exited
        # and the old edit is more than likely closed now
        edit = self.view.begin_edit()

        # Wrap selections with brackets
        style = self._style[value]
        self.insert_regions = []

        for sel in self.view.sel():
            # Determine indentation style
            if style == "indent_block":
                self.block(edit, sel, True)
            elif style == "block":
                self.block(edit, sel)
            else:
                self.inline(edit, sel)

        self.select(edit)

        self.view.end_edit(edit)

    def wrap_style(self, value):
        """
        Choose insert style for wrapping.
        """

        if value < 0:
            return

        style = []

        self.brackets = self._brackets[value]
        for s in VALID_INSERT_STYLES:
            if s[0] in self._insert[value]:
                self._style.append(s[0])
                style.append(s[1])

        if len(style) > 1:
            self.view.window().show_quick_panel(
                style,
                self.wrap_brackets
            )
        else:
            self.wrap_brackets(0)


class WrapBracketsCommand(sublime_plugin.TextCommand, WrapBrackets):
    def run(self, edit):
        """
        Display the wrapping menu
        """

        self._menu = []
        self._brackets = []
        self._insert = []
        self._style = []
        self.read_wrap_entries("bh_wrapping.sublime-settings", "wrapping")

        if len(self._menu):
            self.view.window().show_quick_panel(
                self._menu,
                self.wrap_style
            )


class BhNextWrapSelCommand(sublime_plugin.TextCommand):
    """
    Navigate wrapping tab stop regions
    """

    def run(self, edit):
        """
        Look for the next wrapping tab stop region
        """

        regions = self.view.get_regions(SEL_REGION) + self.view.get_regions(OUT_REGION)
        if len(regions):
            self.view.sel().clear()
            map(lambda x: self.view.sel().add(x), regions)

        # Clean up unneed sections
        self.view.erase_regions(SEL_REGION)
        self.view.erase_regions(OUT_REGION)


class BhWrapListener(sublime_plugin.EventListener):
    """
    Listen for wrapping tab stop tabbing
    """

    def on_query_context(self, view, key, operator, operand, match_all):
        """
        Mark the next regions to navigate to.
        """

        accept_query = False
        if key == "bh_wrapping":
            select = []
            outlier = []
            regions = view.get_regions(TAB_REGION)
            tabstop = []
            sels = view.sel()

            if len(regions) == 0:
                return False

            for s in sels:
                count = 0
                found = False
                for r in regions[:]:
                    if found:
                        select.append(r)
                        tabstop.append(r)
                        del regions[count]
                        break
                    if r.begin() <= s.begin() <= r.end():
                        del regions[count]
                        found = True
                        continue
                    count += 1
                if not found:
                    outlier.append(s)
            tabstop += regions

            if len(tabstop) == len(select):
                if len(tabstop):
                    tabstop = []
                    accept_query = True
            elif len(tabstop) != 0:
                accept_query = True

            # Mark regions to make the "next" command aware of what to do
            view.add_regions(SEL_REGION, select, "", "", sublime.HIDDEN)
            view.add_regions(OUT_REGION, outlier, "", "", sublime.HIDDEN)
            view.add_regions(TAB_REGION, tabstop, "", "", sublime.HIDDEN)

        return accept_query
