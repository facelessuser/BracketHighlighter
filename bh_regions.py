"""
BracketHighlighter.

Copyright (c) 2013 - 2016 Isaac Muse <isaacmuse@gmail.com>
License: MIT
"""
import sublime


DEFAULT_STYLES = {
    "default": {
        "icon": "dot",
        "color": "brackethighlighter.default",
        "style": "underline"
    },
    "unmatched": {
        "icon": "question",
        "color": "brackethighlighter.unmatched",
        "style": "outline"
    }
}
HV_RSVD_VALUES = ["__default__", "__bracket__"]


def underline(regions):
    """Convert sublime regions into underline regions."""

    r = []
    for region in regions:
        start = region.begin()
        end = region.end()
        while start < end:
            r.append(sublime.Region(start))
            start += 1
    return r


def clear_all_regions():
    """Clear all regions."""

    for window in sublime.windows():
        for view in window.views():
            for region_key in view.settings().get("bracket_highlighter.regions", []):
                view.erase_regions(region_key)
            view.settings().set(
                'bracket_highlighter.locations', {'open': {}, 'close': {}, 'unmatched': {}, 'icon': {}}
            )


def select_bracket_style(option, minimap):
    """Configure style of region based on option."""

    style = 0
    if not minimap:
        style |= sublime.HIDE_ON_MINIMAP
    if option == "outline":
        style |= sublime.DRAW_NO_FILL
    elif option == "none":
        style |= sublime.HIDDEN
    elif option == "underline":
        style |= sublime.DRAW_EMPTY_AS_OVERWRITE
    elif option == "thin_underline":
        style |= sublime.DRAW_NO_FILL
        style |= sublime.DRAW_NO_OUTLINE
        style |= sublime.DRAW_SOLID_UNDERLINE
    elif option == "squiggly":
        style |= sublime.DRAW_NO_FILL
        style |= sublime.DRAW_NO_OUTLINE
        style |= sublime.DRAW_SQUIGGLY_UNDERLINE
    elif option == "stippled":
        style |= sublime.DRAW_NO_FILL
        style |= sublime.DRAW_NO_OUTLINE
        style |= sublime.DRAW_STIPPLED_UNDERLINE
    return style


def select_bracket_icons(option, icon_path):
    """Configure custom gutter icons if they can be located."""

    icon = ""
    small_icon = ""
    open_icon = ""
    small_open_icon = ""
    close_icon = ""
    small_close_icon = ""
    # Icon exist?
    if not option == "none" and not option == "":
        try:
            pth = "%s/%s.png" % (icon_path, option)
            sublime.load_binary_resource(pth)
            icon = pth
        except Exception:
            pass
        try:
            pth = "%s/%s_small.png" % (icon_path, option)
            sublime.load_binary_resource(pth)
            small_icon = pth
        except Exception:
            pass
        try:
            pth = "%s/%s_open.png" % (icon_path, option)
            sublime.load_binary_resource(pth)
            open_icon = pth
        except Exception:
            open_icon = icon
        try:
            pth = "%s/%s_open_small.png" % (icon_path, option)
            sublime.load_binary_resource(pth)
            small_open_icon = pth
        except Exception:
            small_open_icon = small_icon
        try:
            pth = "%s/%s_close.png" % (icon_path, option)
            sublime.load_binary_resource(pth)
            close_icon = pth
        except Exception:
            close_icon = icon
        try:
            pth = "%s/%s_close_small.png" % (icon_path, option)
            sublime.load_binary_resource(pth)
            small_close_icon = pth
        except Exception:
            small_close_icon = small_icon

    return icon, small_icon, open_icon, small_open_icon, close_icon, small_close_icon


def get_bracket_regions(settings, minimap):
    """Get styled regions for brackets to use."""

    styles = settings.get("bracket_styles", DEFAULT_STYLES)
    icon_path = "Packages/BracketHighlighter/icons"
    # Make sure default and unmatched styles in styles
    for key, value in DEFAULT_STYLES.items():
        if key not in styles:
            styles[key] = value
            continue
        for k, v in value.items():
            if k not in styles[key]:
                styles[key][k] = v
    # Initialize styles
    default_settings = styles["default"]
    for k, v in styles.items():
        yield k, StyleDefinition(k, v, default_settings, icon_path, minimap)


class StyleDefinition(object):
    """Styling definition."""

    def __init__(self, name, style, default_highlight, icon_path, minimap):
        """
        Setup the style object.

        Setup by reading the passed in dictionary. And other parameters.
        """

        self.name = name
        self.color = style.get("color", default_highlight["color"])
        self.style = select_bracket_style(style.get("style", default_highlight["style"]), minimap)
        self.underline = self.style & sublime.DRAW_EMPTY_AS_OVERWRITE
        self.endpoints = style.get("endpoints", False)
        (
            self.icon, self.small_icon, self.open_icon,
            self.small_open_icon, self.close_icon, self.small_close_icon
        ) = select_bracket_icons(style.get("icon", default_highlight["icon"]), icon_path)
        self.no_icon = ""
        self.clear()

    def clear(self):
        """Clear tracked selections."""

        self.selections = []
        self.open_selections = []
        self.close_selections = []
        self.center_selections = []
        self.content_selections = []


class BhRegion(object):
    """Class for handling highlight regions."""

    def __init__(self, alter_select, count_lines):
        """Init."""

        settings = sublime.load_settings("bh_core.sublime-settings")
        minimap = settings.get('show_in_minimap', False)
        self.log_regions = {'open': {}, 'close': {}, 'unmatched': {}, 'icon': {}}
        self.log_count = 0
        self.count_lines = count_lines
        self.hv_style = select_bracket_style(settings.get("high_visibility_style", "outline"), minimap)
        self.hv_underline = self.hv_style & sublime.DRAW_EMPTY_AS_OVERWRITE
        self.hv_color = settings.get("high_visibility_color", HV_RSVD_VALUES[1])
        self.no_multi_select_icons = bool(settings.get("no_multi_select_icons", False))
        self.bracket_regions = {}
        self.alter_select = alter_select
        for style, bracket_region in get_bracket_regions(settings, minimap):
            self.bracket_regions[style] = bracket_region
        self.set_show_unmatched()

    def get_color(self, bracket_color, high_visibility):
        """Get color."""

        if high_visibility:
            color = self.hv_color
            if self.hv_color == HV_RSVD_VALUES[0]:
                color = self.bracket_regions["default"].color
            elif self.hv_color == HV_RSVD_VALUES[1]:
                color = bracket_color
        else:
            color = bracket_color
        return color

    def set_show_unmatched(self, language=None):
        """Determine if show_unmatched should be enabled for the current view."""

        settings = sublime.load_settings("bh_core.sublime-settings")
        show_unmatched = bool(settings.get("show_unmatched", True))
        exceptions = settings.get("show_unmatched_exceptions", [])
        if isinstance(exceptions, list) and language is not None:
            for option in exceptions:
                if option.lower() == language:
                    show_unmatched = not show_unmatched
                    break
        self.show_unmatched = show_unmatched

    def reset(self, view, num_sels):
        """Reset."""

        self.chars = 0
        self.lines = 0
        self.multi_select = num_sels > 1
        self.sels = []
        self.view = view
        self.log_regions = {'open': {}, 'close': {}, 'unmatched': {}, 'icon': {}}
        self.log_count = 0

        for r in self.bracket_regions.values():
            r.clear()

    def store_sel(self, regions):
        """Store the current selection to be set at the end."""

        if self.alter_select:
            for region in regions:
                self.sels.append(region)

    def change_sel(self):
        """Change the view's selections."""

        if self.alter_select and len(self.sels) > 0:
            if self.multi_select is False:
                self.view.show(self.sels[0])
            self.view.sel().clear()
            self.view.sel().add_all(self.sels)

    def save_incomplete_regions(self, left, right, regions):
        """Store single incomplete brackets for highlighting."""

        found = left if left is not None else right
        bracket = self.bracket_regions["unmatched"]
        if bracket.underline:
            bracket.selections += underline((found.toregion(),))
        else:
            bracket.selections += [found.toregion()]
        self.log_regions['unmatched'][str(self.log_count + 1)] = (found.begin, found.end)
        self.log_count += 1
        self.store_sel(regions)

    def save_regions(self, left, right, regions, style, high_visibility):
        """
        Saved (un)matched regions.

        Perform any special considerations for region formatting.
        """

        handled = False
        if left is not None and right is not None:
            self.save_complete_regions(left, right, regions, style, high_visibility)
            handled = True
        elif (left is not None or right is not None) and self.show_unmatched:
            self.save_incomplete_regions(left, right, regions)
            handled = True
        return handled

    def save_complete_regions(self, left, right, regions, style, high_visibility):
        """Saved matched regions."""

        bracket = self.bracket_regions.get(style, self.bracket_regions["default"])
        lines = abs(self.view.rowcol(right.begin)[0] - self.view.rowcol(left.end)[0] + 1)
        if self.count_lines:
            self.chars += abs(right.begin - left.end)
            self.lines += lines
        if high_visibility:
            self.save_high_visibility_regions(left, right, bracket, lines)
        elif bracket.endpoints:
            self.save_endpoint_regions(left, right, bracket, lines)
        elif bracket.underline:
            self.save_underline_regions(left, right, bracket, lines)
        else:
            self.save_normal_regions(left, right, bracket, lines)

        if sublime.load_settings("bh_core.sublime-settings").get("content_highlight_bar", False) and lines > 1:
            self.save_content_regions(left, right, bracket, lines)

        begin_region = None if left is None else (left.begin, left.end)
        end_region = None if right is None else (right.begin, right.end)
        if begin_region:
            self.log_regions['open'][str(self.log_count + 1)] = begin_region
        if end_region:
            self.log_regions['close'][str(self.log_count + 1)] = end_region
        if begin_region or end_region:
            self.log_regions['icon'][str(self.log_count + 1)] = (
                bracket.icon,
                self.get_color(bracket.color, high_visibility),
            )
            self.log_count += 1

        self.store_sel(regions)

    def save_content_regions(self, left, right, bracket, lines):
        """Calculate content bar location and save region(s)."""

        first_line = self.view.rowcol(left.begin)[0]
        last_line = first_line + lines - 1
        whitespace = (' ', '\t')
        bracket_locations = (left.begin, right.begin)

        if sublime.load_settings("bh_core.sublime-settings").get("align_content_highlight_bar", False):
            start_pt = self.view.text_point(first_line, 0)
            end_pt = left.end
            tab_size = self.view.settings().get("tab_size", 4)
            index = 0
            tabs = 0
            count = 0
            # Calculate column index of where text starts for line
            # containing opening bracket
            for x in range(start_pt, start_pt + end_pt):
                char = self.view.substr(x)
                if char == "\t":
                    # Track all tabs
                    tabs += 1
                elif char != " ":
                    # Calculate column on first non-whitespace character
                    remainder = count & tab_size
                    tab_aligned = int(count / tab_size)
                    if remainder and tabs:
                        # Index of first non-whitespace character.
                        # Account for smaller tabs that are not aligned on
                        # tab_size boudary.
                        index = tab_aligned + (tabs * (tab_size - 1)) + tab_size
                    else:
                        # Index of first non-whitespace character.
                        # Spaces and full tabs aligned on tab_size boundaries
                        index = count + (tabs * (tab_size - 1))
                    break
                count += 1

            for x in range(first_line + 1, first_line + lines):
                start_pt = self.view.text_point(x, 0)
                end_pt = start_pt + index
                actual_pt = start_pt - 1
                offset = 0
                tab_unit = 0
                include = True

                # Loop through all lines after the first.
                # Calculate the true column postion where the bar should
                # be drawn.  Calculation should account for tabs.
                for y in range(start_pt, start_pt + end_pt):
                    char = self.view.substr(y)
                    if char == '\x00':
                        # Exended past the file's end
                        actual_pt += 1
                        break
                    elif char == "\t":
                        # Tab will expand to the rest of the tab_size.
                        # Track columns that are consumed by tabs.
                        offset += tab_size - 1 - tab_unit
                        tab_unit = tab_size
                        actual_pt += 1
                    elif char == " ":
                        # Normal space.
                        # Track columns consumed by spaces in relation to tab_size.
                        actual_pt += 1
                        tab_unit += 1
                    elif (actual_pt + 1 + offset) < end_pt:
                        # Do not draw bar if text comes before bar
                        include = False
                        break
                    if tab_unit == tab_size:
                        # Roll over tab_unit
                        tab_unit = 0
                    if (actual_pt + offset) >= end_pt:
                        # Reached the target point.
                        break
                if include and (actual_pt - start_pt) + 1 > count and actual_pt < right.begin:
                    if self.view.rowcol(actual_pt)[0] == x and actual_pt not in bracket_locations:
                        if x == last_line:
                            # Draw bar on last line if text comes before bracket
                            include = False
                            for y in range(actual_pt, right.begin):
                                if self.view.substr(y) not in whitespace:
                                    include = True
                                    break
                            if include:
                                bracket.content_selections.append(sublime.Region(actual_pt))
                        else:
                            # Content line; draw bar
                            bracket.content_selections.append(sublime.Region(actual_pt))
        else:
            # Loop through all lines after the first, draw a bar
            for x in range(first_line + 1, first_line + lines):
                pt = self.view.text_point(x, 0)
                if pt not in bracket_locations:
                    if x == last_line:
                        # Draw bar on last line if text comes before bracket
                        include = False
                        for y in range(pt, right.begin):
                            if self.view.substr(y) not in whitespace:
                                include = True
                                break
                        if include:
                            bracket.content_selections.append(sublime.Region(pt))
                    else:
                        # Content line; draw bar
                        bracket.content_selections.append(sublime.Region(pt))

    def save_high_visibility_regions(self, left, right, bracket, lines):
        """Save high visibility regions."""

        if lines <= 1:
            if self.hv_underline:
                bracket.selections += underline((sublime.Region(left.begin, right.end),))
            else:
                bracket.selections += [sublime.Region(left.begin, right.end)]
        else:
            bracket.open_selections += [sublime.Region(left.begin)]
            if self.hv_underline:
                bracket.center_selections += underline((sublime.Region(left.begin + 1, right.end - 1),))
            else:
                bracket.center_selections += [sublime.Region(left.begin, right.end)]
            bracket.close_selections += [sublime.Region(right.begin)]

    def save_endpoint_regions(self, left, right, bracket, lines):
        """Save endpoint regions. Underlined and normal."""

        offset = 0 if bracket.underline else 1
        if lines <= 1:
            bracket.selections += [
                sublime.Region(left.begin, left.begin + offset),
                sublime.Region(right.begin, right.begin + offset)
            ]
            if left.size() > 1:
                bracket.selections += [sublime.Region(left.end - offset, left.end)]
            if right.size() > 1:
                bracket.selections += [sublime.Region(right.end - offset, right.end)]
        else:
            bracket.open_selections += [sublime.Region(left.begin, left.begin + offset)]
            bracket.close_selections += [sublime.Region(right.begin, right.begin + offset)]
            if left.size() > 1:
                bracket.center_selections += [sublime.Region(left.end - offset, left.end)]
            if right.size() > 1:
                bracket.center_selections += [sublime.Region(right.end - offset, right.end)]

    def save_underline_regions(self, left, right, bracket, lines):
        """Save underlined regions."""

        if lines <= 1:
            bracket.selections += underline((left.toregion(), right.toregion()))
        else:
            bracket.open_selections += [sublime.Region(left.begin)]
            bracket.close_selections += [sublime.Region(right.begin)]
            if left.size():
                bracket.center_selections += underline((sublime.Region(left.begin + 1, left.end),))
            if right.size():
                bracket.center_selections += underline((sublime.Region(right.begin + 1, right.end),))

    def save_normal_regions(self, left, right, bracket, lines):
        """Save normal regions."""

        if lines <= 1:
            bracket.selections += [left.toregion(), right.toregion()]
        else:
            bracket.open_selections += [left.toregion()]
            bracket.close_selections += [right.toregion()]

    def highlight_regions(self, name, icon_type, selections, bracket, regions, high_visibility):
        """Apply the highlightes for the highlight region."""

        if len(selections):
            if selections == "content_selections":
                self.view.add_regions(
                    name,
                    getattr(bracket, selections) if not high_visibility else [],
                    self.get_color(bracket.color, False),
                    getattr(bracket, icon_type),
                    sublime.DRAW_EMPTY
                )
            else:
                self.view.add_regions(
                    name,
                    getattr(bracket, selections),
                    self.get_color(bracket.color, high_visibility),
                    getattr(bracket, icon_type),
                    self.hv_style if high_visibility else bracket.style
                )
            regions.append(name)

    def highlight(self, high_visibility):
        """Highlight all bracket regions."""

        self.change_sel()

        for region_key in self.view.settings().get("bracket_highlighter.regions", []):
            self.view.erase_regions(region_key)
            self.view.settings().set(
                'bracket_highlighter.locations', {'open': {}, 'close': {}, 'unmatched': {}, 'icon': {}}
            )

        regions = []
        icon_type = "no_icon"
        open_icon_type = "no_icon"
        close_icon_type = "no_icon"
        if not self.no_multi_select_icons or not self.multi_select:
            icon_type = "small_icon" if self.view.line_height() < 16 else "icon"
            open_icon_type = "small_open_icon" if self.view.line_height() < 16 else "open_icon"
            close_icon_type = "small_close_icon" if self.view.line_height() < 16 else "close_icon"
        for name, r in self.bracket_regions.items():
            self.highlight_regions(
                "bh_" + name, icon_type, "selections", r, regions, high_visibility
            )
            self.highlight_regions(
                "bh_" + name + "_center", "no_icon", "center_selections", r, regions, high_visibility
            )
            self.highlight_regions(
                "bh_" + name + "_open", open_icon_type, "open_selections", r, regions, high_visibility
            )
            self.highlight_regions(
                "bh_" + name + "_close", close_icon_type, "close_selections", r, regions, high_visibility
            )
            self.highlight_regions(
                "bh_" + name + "_content", "no_icon", "content_selections", r, regions, high_visibility
            )
        # Track which regions were set in the view so that they can be cleaned up later.
        self.view.settings().set("bracket_highlighter.regions", regions)
        self.view.settings().set("bracket_highlighter.locations", self.log_regions)

        if self.count_lines:
            sublime.status_message('In Block: Lines ' + str(self.lines) + ', Chars ' + str(self.chars))
