import sublime
from os.path import normpath, exists, join


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
    """
    Convert sublime regions into underline regions
    """

    r = []
    for region in regions:
        start = region.begin()
        end = region.end()
        while start < end:
            r.append(sublime.Region(start))
            start += 1
    return r


def select_bracket_style(option):
    """
    Configure style of region based on option
    """

    style = sublime.HIDE_ON_MINIMAP
    if option == "outline":
        style |= sublime.DRAW_OUTLINED
    elif option == "none":
        style |= sublime.HIDDEN
    elif option == "underline":
        style |= sublime.DRAW_EMPTY_AS_OVERWRITE
    return style


def select_bracket_icons(option, icon_path):
    """
    Configure custom gutter icons if they can be located.
    """

    icon = ""
    small_icon = ""
    open_icon = ""
    small_open_icon = ""
    close_icon = ""
    small_close_icon = ""
    # Icon exist?
    if not option == "none" and not option == "":
        if exists(normpath(join(sublime.packages_path(), icon_path, option + ".png"))):
            icon = "../%s/%s" % (icon_path, option)
        if exists(normpath(join(sublime.packages_path(), icon_path, option + "_small.png"))):
            small_icon = "../%s/%s" % (icon_path, option + "_small")
        if exists(normpath(join(sublime.packages_path(), icon_path, option + "_open.png"))):
            open_icon = "../%s/%s" % (icon_path, option + "_open")
        else:
            open_icon = icon
        if exists(normpath(join(sublime.packages_path(), icon_path, option + "_open_small.png"))):
            small_open_icon = "../%s/%s" % (icon_path, option + "_open_small")
        else:
            small_open_icon = small_icon
        if exists(normpath(join(sublime.packages_path(), icon_path, option + "_close.png"))):
            close_icon = "../%s/%s" % (icon_path, option + "_close")
        else:
            close_icon = icon
        if exists(normpath(join(sublime.packages_path(), icon_path, option + "_close_small.png"))):
            small_close_icon = "../%s/%s" % (icon_path, option + "_close_small")
        else:
            small_close_icon = small_icon

    return icon, small_icon, open_icon, small_open_icon, close_icon, small_close_icon


def get_bracket_regions(settings):
    """
    Get styled regions for brackets to use.
    """

    styles = settings.get("bracket_styles", DEFAULT_STYLES)
    icon_path = "BracketHighlighter/icons"
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
        yield k, StyleDefinition(k, v, default_settings, icon_path)


class StyleDefinition(object):
    """
    Styling definition.
    """

    def __init__(self, name, style, default_highlight, icon_path):
        """
        Setup the style object by reading the
        passed in dictionary. And other parameters.
        """

        self.name = name
        self.color = style.get("color", default_highlight["color"])
        self.style = select_bracket_style(style.get("style", default_highlight["style"]))
        self.underline = self.style & sublime.DRAW_EMPTY_AS_OVERWRITE
        self.endpoints = style.get("endpoints", False)
        (
            self.icon, self.small_icon, self.open_icon,
            self.small_open_icon, self.close_icon, self.small_close_icon
        ) = select_bracket_icons(style.get("icon", default_highlight["icon"]), icon_path)
        self.no_icon = ""
        self.clear()

    def clear(self):
        """
        Clear tracked selections
        """

        self.selections = []
        self.open_selections = []
        self.close_selections = []
        self.center_selections = []


class BhRegion(object):
    def __init__(self, alter_select, count_lines):
        settings = sublime.load_settings("bh_core.sublime-settings")
        self.count_lines = count_lines
        self.hv_style = select_bracket_style(settings.get("high_visibility_style", "outline"))
        self.hv_underline = self.hv_style & sublime.DRAW_EMPTY_AS_OVERWRITE
        self.hv_color = settings.get("high_visibility_color", HV_RSVD_VALUES[1])
        self.no_multi_select_icons = bool(settings.get("no_multi_select_icons", False))
        self.bracket_regions = {}
        self.alter_select = alter_select
        for style, bracket_region in get_bracket_regions(settings):
            self.bracket_regions[style] = bracket_region
        self.set_show_unmatched()

    def get_color(self, bracket_color, high_visibility):
        """
        Get color
        """

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
        """
        Determine if show_unmatched should be enabled for the current view
        """

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
        """
        Reset
        """

        self.chars = 0
        self.lines = 0
        self.multi_select = num_sels > 1
        self.sels = []
        self.view = view

        for r in self.bracket_regions.values():
            r.clear()

    def store_sel(self, regions):
        """
        Store the current selection to be set at the end.
        """

        if self.alter_select:
            for region in regions:
                self.sels.append(region)

    def change_sel(self):
        """
        Change the view's selections.
        """

        if self.alter_select and len(self.sels) > 0:
            if self.multi_select is False:
                self.view.show(self.sels[0])
            self.view.sel().clear()
            map(lambda x: self.view.sel().add(x), self.sels)

    def save_incomplete_regions(self, left, right, regions):
        """
        Store single incomplete brackets for highlighting.
        """

        found = left if left is not None else right
        bracket = self.bracket_regions["unmatched"]
        if bracket.underline:
            bracket.selections += underline((found.toregion(),))
        else:
            bracket.selections += [found.toregion()]
        self.store_sel(regions)

    def save_regions(self, left, right, regions, style, high_visibility):
        """
        Saved (un)matched regions.  Perform any special considerations for region formatting.
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
        """
        Saved matched regions.
        """

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
        self.store_sel(regions)

    def save_high_visibility_regions(self, left, right, bracket, lines):
        """
        Save high visibility regions.
        """

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
        """
        Save endpoint regions. Underlined and normal.
        """

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
        """
        Save underlined regions
        """

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
        """
        Save normal regions
        """

        if lines <= 1:
            bracket.selections += [left.toregion(), right.toregion()]
        else:
            bracket.open_selections += [left.toregion()]
            bracket.close_selections += [right.toregion()]

    def highlight_regions(self, name, icon_type, selections, bracket, regions, high_visibility):
        """
        Apply the highlightes for the highlight region.
        """

        if len(selections):
            self.view.add_regions(
                name,
                getattr(bracket, selections),
                self.get_color(bracket.color, high_visibility),
                getattr(bracket, icon_type),
                self.hv_style if high_visibility else bracket.style
            )
            regions.append(name)

    def highlight(self, high_visibility):
        """
        Highlight all bracket regions.
        """

        self.change_sel()

        for region_key in self.view.settings().get("bh_regions", []):
            self.view.erase_regions(region_key)

        regions = []
        icon_type = "no_icon"
        open_icon_type = "no_icon"
        close_icon_type = "no_icon"
        if not self.no_multi_select_icons or not self.multi_select:
            icon_type = "small_icon" if self.view.line_height() < 16 else "icon"
            open_icon_type = "small_open_icon" if self.view.line_height() < 16 else "open_icon"
            close_icon_type = "small_close_icon" if self.view.line_height() < 16 else "close_icon"
        for name, r in self.bracket_regions.items():
            self.highlight_regions("bh_" + name, icon_type, "selections", r, regions, high_visibility)
            self.highlight_regions("bh_" + name + "_center", "no_icon", "center_selections", r, regions, high_visibility)
            self.highlight_regions("bh_" + name + "_open", open_icon_type, "open_selections", r, regions, high_visibility)
            self.highlight_regions("bh_" + name + "_close", close_icon_type, "close_selections", r, regions, high_visibility)
        # Track which regions were set in the view so that they can be cleaned up later.
        self.view.settings().set("bh_regions", regions)

        if self.count_lines:
            sublime.status_message('In Block: Lines ' + str(self.lines) + ', Chars ' + str(self.chars))
