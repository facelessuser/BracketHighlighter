from os.path import basename
from random import randrange
from Elements import is_tag, match
import sublime
import sublime_plugin
from bracket_plugin import BracketPlugin

BH_MATCH_TYPE_NONE = 0
BH_MATCH_TYPE_SELECTION = 1
BH_MATCH_TYPE_EDIT = 2


class BracketHighlighterKeyCommand(sublime_plugin.WindowCommand):
    def run(self, threshold=True, lines=False, adjacent=False, ignore={}, plugin={}):
        BracketHighlighterCommand(
            threshold,
            lines,
            adjacent,
            ignore,
            plugin
        ).match(self.window.active_view())


class BracketHighlighterCommand(sublime_plugin.EventListener):
    # Initialize
    def __init__(self, override_thresh=False, count_lines=False, adj_only=None, ignore={}, plugin={}):
        self.settings = sublime.load_settings("BracketHighlighter.sublime-settings")
        self.settings.add_on_change('reload', lambda: self.setup())
        self.setup(override_thresh, count_lines, adj_only, ignore, plugin)
        self.debounce_id = 0
        self.debounce_type = 0

    def setup(self, override_thresh=False, count_lines=False, adj_only=None, ignore={}, plugin={}):
        self.last_id_view = None
        self.last_id_sel = None
        self.targets = []
        self.sels = []
        self.highlight_us = {}
        self.brackets = self.init_brackets()
        self.lines = 0
        self.chars = 0
        self.count_lines = count_lines
        self.ignore_angle = bool(self.settings.get('ignore_non_tags'))
        self.tag_type = self.settings.get('tag_type')
        self.new_select = False
        self.debounce_delay = int(self.settings.get('debounce_delay', 1000))

        # On demand ignore
        self.ignore = ignore

        # Setup for bracket plugins
        self.transform = {
            'quote':   False,
            'bracket': False,
            'tag':     False
        }

        if 'command' in plugin:
            self.plugin = BracketPlugin(plugin)
            self.new_select = True
            if 'type' in plugin:
                if 'quote' in plugin['type']:
                    self.transform['quote'] = True
                if 'bracket' in plugin['type']:
                    self.transform['bracket'] = True
                if 'tag' in plugin['type']:
                    self.transform['tag'] = True

        # Search threshold
        self.adj_only = adj_only if adj_only != None else bool(self.settings.get('match_adjacent_only'))
        self.use_threshold = False if override_thresh else bool(self.settings.get('use_search_threshold'))
        self.tag_use_threshold = False if override_thresh else bool(self.settings.get('tag_use_search_threshold'))
        self.search_threshold = int(self.settings.get('search_threshold'))
        self.tag_search_threshold = int(self.settings.get('tag_search_threshold'))

        # Tag special options
        self.brackets_only = bool(self.settings.get('tag_brackets_only'))

    def init_brackets(self):
        return {
            'bh_curly':  self.get_bracket_settings('curly', '{', '}'),
            'bh_round':  self.get_bracket_settings('round', '(', ')'),
            'bh_square': self.get_bracket_settings('square', '[', ']'),
            'bh_angle':  self.get_bracket_settings('angle', '<', '>'),
            'bh_tag':    self.get_bracket_settings('tag', '<', '>'),
            'bh_quote':  self.get_bracket_settings('quote', "'", "'")
        }

    def get_bracket_settings(self, bracket, opening, closing):
        style = sublime.HIDE_ON_MINIMAP
        if self.settings.get(bracket + '_style') == "outline":
            style |= sublime.DRAW_OUTLINED
        elif self.settings.get(bracket + '_style') == "none":
            style |= sublime.HIDDEN
        elif self.settings.get(bracket + '_style') == "underline":
            style |= sublime.DRAW_EMPTY_AS_OVERWRITE
        return {
            'enable':    bool(self.settings.get(bracket + '_enable')),
            'scope':     self.settings.get(bracket + '_scope'),
            'style':     style,
            'underline': (self.settings.get(bracket + '_style') == "underline"),
            'icon':      self.settings.get(bracket + '_icon'),
            'list':      map(lambda x: x.lower(), self.settings.get(bracket + '_language_list')),
            'filter':    self.settings.get(bracket + '_language_filter'),
            'open':      opening,
            'close':     closing
        }

    def init_match(self):
        # Current language
        syntax = self.view.settings().get('syntax')
        language = basename(syntax).replace('.tmLanguage', '').lower() if syntax != None else "plain text"
        # Reset objects
        self.sels = []
        self.targets = []
        self.highlight_us = {}
        self.lines = 0
        self.multi_select = False
        self.adj_bracket = False

        # Standard Brackets
        if self.exclude_bracket('bh_curly', language) == False:
            self.add_bracket('bh_curly')
        if self.exclude_bracket('bh_round', language) == False:
            self.add_bracket('bh_round')
        if self.exclude_bracket('bh_square', language) == False:
            self.add_bracket('bh_square')
        if self.exclude_bracket('bh_angle', language) == False:
            self.add_bracket('bh_angle')
        # Tags
        if self.exclude_bracket('bh_tag', language) == False:
            self.tag_enable = True
            self.highlight_us['bh_tag'] = []
        else:
            self.tag_enable = False
        # Quotes
        if self.exclude_bracket('bh_quote', language) == False:
            self.quote_enable = True
            self.highlight_us['bh_quote'] = []
        else:
            self.quote_enable = False

    def add_bracket(self, bracket):
        self.highlight_us[bracket] = []
        self.targets.append(bracket)

    def exclude_bracket(self, bracket, language):
        exclude = True
        if bracket.replace('bh_', '') in self.ignore:
            return exclude
        if self.brackets[bracket]['enable']:
            # Black list languages
            if self.brackets[bracket]['filter'] == 'blacklist':
                exclude = False
                if language != None:
                    for item in self.brackets[bracket]['list']:
                        if language == item:
                            exclude = True
                            break
            #White list languages
            elif self.brackets[bracket]['filter'] == 'whitelist':
                if language != None:
                    for item in self.brackets[bracket]['list']:
                        if language == item:
                            exclude = False
                            break
        return exclude

    def unique(self):
        id_view = self.view.id()
        id_sel = ''
        is_unique = False
        for sel in self.view.sel():
            id_sel += str(sel.a)
        if id_view != self.last_id_view or id_sel != self.last_id_sel:
            self.last_id_view = id_view
            self.last_id_sel = id_sel
            is_unique = True
        return is_unique

    def highlight(self, view):
        # Perform highlight on brackets and tags
        for bracket in self.brackets:
            if bracket in self.highlight_us:
                view.add_regions(
                    bracket,
                    self.highlight_us[bracket],
                    self.brackets[bracket]['scope'],
                    self.brackets[bracket]['icon'],
                    self.brackets[bracket]['style']
                )
            else:
                view.erase_regions(bracket)

    def store_sel(self, regions):
        if self.new_select == True:
            for region in regions:
                self.sels.append(region)

    def change_sel(self):
        if self.new_select != None and len(self.sels) > 0:
            if self.multi_select == False:
                self.view.show(self.sels[0])
            self.view.sel().clear()
            map(lambda x: self.view.sel().add(x), self.sels)

    def adjacent_adjust(self, scout):
        # Offset cursor
        offset = 0
        allow_quote_match = True
        # If quotes enbaled, kick out of adjacent check if in middle of string
        if (
            self.view.score_selector(scout, 'string') > 0 and
            self.view.score_selector(scout - 1, 'string') > 0 and
            self.quote_enable
        ):
            return (offset, allow_quote_match)
        if offset == 0:
            char1 = self.view.substr(scout - 1)
            char2 = self.view.substr(scout)
            for bracket in self.targets:
                if char2 == self.brackets[bracket]['open']:
                    self.adj_bracket = True
                if char1 == self.brackets[bracket]['open']:
                    offset = -1
                    self.adj_bracket = True
                    allow_quote_match = False
                    break
                elif char1 == self.brackets[bracket]['close']:
                    offset = -2
                    self.adj_bracket = True
                    allow_quote_match = False
                elif char2 == self.brackets[bracket]['close'] and offset != -2:
                    offset = -1
                    self.adj_bracket = True
                    allow_quote_match = True
        if offset == 0:
            allow_quote_match = True
        return (offset, allow_quote_match)

    def match(self, view, force_match=True):
        if view == None:
            return
        # Setup views
        self.view = view
        self.last_view = view
        self.multi_select = (len(view.sel()) > 1)

        if self.unique() or force_match:
            # Initialize
            self.init_match()

            # Process selections.
            for sel in view.sel():
                self.find_matches(sel)

        # Highlight, focus, and display lines etc.
        self.change_sel()
        self.highlight(view)
        if self.count_lines:
            sublime.status_message('In Block: Lines ' + str(self.lines) + ', Chars ' + str(self.chars))

    def find_matches(self, sel):
        (offset, allow_quote_match) = self.adjacent_adjust(sel.a)
        start = sel.a
        matched = False
        is_string = False
        self.search_left = self.search_threshold

        # Match quotes if enabled
        if self.quote_enable and allow_quote_match:
            (matched, start, is_string) = self.match_quotes(sel)
            # Found quotes; exit
            if matched:
                return

        # Special considerations for cusrsor adjacent to bracket
        if matched == False and is_string == False:
            start += offset
        # If not adjacent to bracket and adjacent enabled, exit
        if self.adj_only:
            if not self.adj_bracket:
                return

        # Find left brace
        left = self.scout_left(start)
        if left != None:
            for bracket in self.targets:
                if self.view.substr(left) == self.brackets[bracket]['open']:
                    self.bracket_type = bracket
                    self.bracket_open = self.brackets[bracket]['open']
                    self.bracket_close = self.brackets[bracket]['close']
                    break
            # Find right brace
            right = self.scout_right(start + 1)

        regions = [sublime.Region(sel.a, sel.b)]

        # Bracket Matches found
        if left != None and right != None:
            # Angle specific
            if self.bracket_type == 'bh_angle':
                # Find tags if required
                if (
                    self.tag_enable and
                    is_tag(self.view.substr(sublime.Region(left, right + 1)))
                ):
                    # Found tag; quit
                    if self.match_tags(left, right, sel):
                        return
                # Continue higlighting angle unless required not to
                if self.ignore_angle:
                    self.store_sel(regions)
                    return

            # Set higlight regions
            if (
                self.transform['bracket'] and
                self.plugin != None and
                self.plugin.is_enabled()
            ):
                (b_region, c_region, regions) = self.plugin.run_command(
                    sublime.Region(left, right + 1),
                    sublime.Region(left + 1, right),
                    regions
                )
                left = b_region.a
                right = b_region.b - 1
            if self.brackets[self.bracket_type]['underline']:
                self.highlight_us[self.bracket_type].append(sublime.Region(left))
                self.highlight_us[self.bracket_type].append(sublime.Region(right))
            else:
                self.highlight_us[self.bracket_type].append(sublime.Region(left, left + 1))
                self.highlight_us[self.bracket_type].append(sublime.Region(right, right + 1))
            if self.count_lines:
                self.lines += self.view.rowcol(right)[0] - self.view.rowcol(left)[0] + 1
                self.chars += right - 1 - left
        self.store_sel(regions)

    def scout_left(self, scout):
        count = {}
        for bracket in self.targets:
            count[bracket] = 0

        while scout >= 0:
            if self.use_threshold:
                self.search_left -= 1
                if self.search_left < 0:
                    return None

            # Are we in a string or comment?
            if (
                self.view.score_selector(scout, 'string') == 0 and
                self.view.score_selector(scout, 'comment') == 0 and
                self.view.score_selector(scout, 'keyword.operator') == 0
            ):
                # Assign char.
                char = self.view.substr(scout)
                # Hit brackets.
                foundBracket = False
                for bracket in self.targets:
                    if char == self.brackets[bracket]['open']:
                        if count[bracket] > 0:
                            count[bracket] -= 1
                            foundBracket = True
                            break
                        else:
                            return scout

                if foundBracket == False:
                    for bracket in self.targets:
                        if char == self.brackets[bracket]['close']:
                            count[bracket] += 1
                            break
            scout -= 1

    def scout_right(self, scout):
        brackets = 0
        viewSize = self.view.size()

        while scout < viewSize:
            if self.use_threshold:
                self.search_left -= 1
                if self.search_left < 0:
                    return None
            # Are we in a string or comment?
            if (
                self.view.score_selector(scout, 'string') == 0 and
                self.view.score_selector(scout, 'comment') == 0 and
                self.view.score_selector(scout, 'keyword.operator') == 0
            ):

                # Assign char.
                char = self.view.substr(scout)
                # Hit brackets.
                if char == self.bracket_close:
                    if brackets > 0:
                        brackets -= 1
                    else:
                        return scout
                elif char == self.bracket_open:
                    brackets += 1
            scout += 1

    def match_tags(self, start, end, sel):
        self.search_left = self.tag_search_threshold
        matched = False
        tag_highlights = []

        # Go find tags. Limit search with threshold if required
        bufferSize = self.view.size()
        bufferRegion = sublime.Region(0, bufferSize)
        bufferText = self.view.substr(bufferRegion)
        curPosition = start + 1
        foundTags = match(
            bufferText,
            curPosition,
            self.tag_type,
            self.tag_use_threshold,
            self.search_left
        )

        # Find brackets inside tags
        tag1 = {"match": foundTags[0]}
        tag2 = {"match": foundTags[1]}
        if (
            str(tag1['match']) != 'None' and
            self.view.substr(tag1['match'] + 1) != '!' and
            self.view.substr(tag1['match'] - 1) != '`' and
            self.view.substr(tag1['match']) == '<' and
            self.view.substr(curPosition) != '<'
        ):

            # Get 1st Tag
            matched = True
            # Already have end points?
            if tag1['match'] == start:
                tag1['begin'] = start
                tag1['end'] = end
            # Calculate end points
            else:
                tag1['begin'] = tag1['match']
                tag1['end'] = tag1['match']
                while (
                    self.view.substr(tag1['end']) != '>' or
                    self.view.score_selector(tag1['end'], 'string')
                ):
                    tag1['end'] = tag1['end'] + 1
                    if (
                        self.view.substr(tag1['end']) == '<' and
                        self.view.score_selector(tag1['end'], 'string') == 0
                    ):
                        matched = False

            # Get 2nd Tag
            # Already have end points?
            if tag2['match'] == end + 1:
                tag2['end'] = end
                tag2['begin'] = start
            # Calculate end points
            else:
                tag2['end'] = tag2['match'] - 1
                tag2['begin'] = tag2['end']
                while (
                    self.view.substr(tag2['begin']) != '<' or
                    self.view.score_selector(tag2['begin'], 'string')
                ):
                    tag2['begin'] = tag2['begin'] - 1

            # Set Highlight Region
            if matched:
                regions = [sublime.Region(sel.a, sel.b)]
                if (
                    self.transform['tag'] and
                    self.plugin != None and
                    self.plugin.is_enabled()
                ):
                    (b_region, c_region, regions) = self.plugin.run_command(
                        sublime.Region(tag1['begin'], tag2['end'] + 1),
                        sublime.Region(tag1['end'] + 1, tag2['begin']),
                        regions
                    )
                    tag1['begin'] = b_region.a
                    tag2['end'] = b_region.b - 1
                    tag1['end'] = c_region.a - 1
                    tag2['begin'] = c_region.b

                # Set highlight regions
                if self.brackets_only:
                    tag_highlights = [
                        sublime.Region(tag1['begin'], tag1['begin'] + 1),
                        sublime.Region(tag1['end'], tag1['end'] + 1),
                        sublime.Region(tag2['begin'], tag2['begin'] + 1),
                        sublime.Region(tag2['end'], tag2['end'] + 1)
                    ]
                else:
                    tag_highlights = [
                        sublime.Region(tag1['begin'], tag1['end'] + 1),
                        sublime.Region(tag2['begin'], tag2['end'] + 1)
                    ]

                # Add highlight regions
                if self.brackets['bh_tag']['underline']:
                    self.underline_tag(tag_highlights)
                else:
                    for highlight in tag_highlights:
                        self.highlight_us['bh_tag'].append(highlight)

                if self.count_lines:
                    self.lines += self.view.rowcol(tag2['begin'])[0] - self.view.rowcol(tag1['end'])[0] + 1
                    self.chars += tag2['begin'] - 1 - tag1['end']
                self.store_sel(regions)
        return matched

    def underline_tag(self, regions):
        for region in regions:
            start = region.begin()
            end = region.end()
            while start < end:
                self.highlight_us['bh_tag'].append(sublime.Region(start))
                start += 1

    def match_quotes(self, sel):
        start = sel.a
        matched = False
        bail = False
        is_string = False
        #Check if likely a string
        left_side_match = (self.view.score_selector(start, 'string') > 0)
        right_side_match = (self.view.score_selector(start - 1, 'string') > 0)
        if self.adj_only:
            far_left_side_match = (self.view.score_selector(start - 2, 'string') > 0)
            far_right_side_match = (self.view.score_selector(start + 1, 'string') > 0)
            bail = not (
                (left_side_match or right_side_match) and
                (
                    (left_side_match != right_side_match) or
                    not far_left_side_match or
                    not far_right_side_match
                )
            )
        if (left_side_match or right_side_match) and bail == False:
            # Calculate offset
            is_string = True
            offset = -1 if left_side_match == False else 0
            (matched, start) = self.find_quotes(start + offset, sel)
        return (matched, start, is_string)

    def find_quotes(self, start, sel):
        begin = start
        end = start
        scout = start
        quote = None
        lastChar = None
        matched = False

        # Left quote
        while scout >= 0:
            if self.use_threshold:
                self.search_left -= 1
                if self.search_left < 0:
                    return (matched, scout)
            char = self.view.substr(scout)
            if self.view.score_selector(scout, 'string') > 0:
                if scout == 0:
                    begin = scout
                    if char == "'" or char == '"':
                        quote = char
                    break
                else:
                    scout -= 1
                    lastChar = char
            else:
                begin = scout + 1
                if lastChar == "'" or lastChar == '"':
                    quote = lastChar
                break

        # If quote fails continue off from furthest left
        # to find other brackets
        search_left = self.search_left
        self.search_left += 1

        # Right quote
        if quote != None:
            scout = start
            viewSize = self.view.size() - 1
            lastChar = None
            while scout <= viewSize:
                if self.use_threshold:
                    search_left -= 1
                    if search_left < 0:
                        self.search_left = -1
                        return (matched, begin - 1)
                char = self.view.substr(scout)
                if self.view.score_selector(scout, 'string') > 0:
                    if scout == viewSize:
                        if char == quote and scout != begin:
                            end = scout + 1
                            matched = True
                        break
                    else:
                        scout += 1
                        lastChar = char
                else:
                    if lastChar == quote and scout - 1 != begin:
                        end = scout
                        matched = True
                    break

        if matched:
            regions = [sublime.Region(sel.a, sel.b)]
            if (
                self.transform['quote'] and
                self.plugin != None and
                self.plugin.is_enabled()
            ):
                (b_region, c_region, regions) = self.plugin.run_command(
                    sublime.Region(begin, end),
                    sublime.Region(begin + 1, end - 1),
                    regions
                )
                begin = b_region.a
                end = b_region.b
            if self.brackets['bh_quote']['underline']:
                self.highlight_us['bh_quote'].append(sublime.Region(begin))
                self.highlight_us['bh_quote'].append(sublime.Region(end - 1))
            else:
                self.highlight_us['bh_quote'].append(sublime.Region(begin, begin + 1))
                self.highlight_us['bh_quote'].append(sublime.Region(end - 1, end))
            if self.count_lines:
                self.lines += self.view.rowcol(end)[0] - self.view.rowcol(begin)[0] + 1
                self.chars += end - 2 - begin
            self.store_sel(regions)
        return (matched, begin - 1)

    def check_debounce(self, debounce_id):
        if self.debounce_id != debounce_id:
            debounce_id = randrange(1, 999999)
            self.debounce_id = debounce_id
            sublime.set_timeout(
                lambda: self.check_debounce(debounce_id=debounce_id),
                self.debounce_delay
            )
        else:
            self.debounce_id = 0
            force_match = True if self.debounce_type == BH_MATCH_TYPE_EDIT else False
            self.debounce_type = BH_MATCH_TYPE_NONE
            self.match(sublime.active_window().active_view(), force_match)

    def debounce(self, debounce_type):
        # Check if debunce not currently active, or if of same type,
        # but let edit override selection for undos
        if (
            self.debounce_type == BH_MATCH_TYPE_NONE or
            debounce_type == BH_MATCH_TYPE_EDIT or
            self.debounce_type == debounce_type
        ):
            self.debounce_type = debounce_type
            debounce_id = randrange(1, 999999)
            if self.debounce_id == 0:
                self.debounce_id = debounce_id
                sublime.set_timeout(
                    lambda: self.check_debounce(debounce_id=debounce_id),
                    self.debounce_delay
                )
            else:
                self.debounce_id = debounce_id

    def on_load(self, view):
        self.debounce(BH_MATCH_TYPE_SELECTION)

    def on_modified(self, view):
        self.debounce(BH_MATCH_TYPE_EDIT)

    def on_activated(self, view):
        self.debounce(BH_MATCH_TYPE_SELECTION)

    def on_selection_modified(self, view):
        self.debounce(BH_MATCH_TYPE_SELECTION)
