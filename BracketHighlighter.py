from os.path import basename
from Elements import is_tag, match
import sublime, sublime_plugin

class BracketHighlighterKeyCommand(sublime_plugin.WindowCommand):
  def run(self,show=None):
    BracketHighlighterCommand(True,True,show,False).match(self.window.active_view())

class BracketHighlighterCommand(sublime_plugin.EventListener):
  # Initialize
  def __init__(self, override_thresh=False, count_lines=False, show=None, adj_only=None):
    self.settings = sublime.load_settings('BracketHighlighter.sublime-settings')
    self.settings.add_on_change('reload', lambda: self.setup())
    self.setup(override_thresh,count_lines,show,adj_only)

  def setup(self,override_thresh=False, count_lines=False, show=None, adj_only=None):
    self.last_id_view                 = None
    self.last_id_sel                  = None
    self.targets                      = []
    self.sels                         = []
    self.highlight_us                 = {}
    self.brackets                     = self.init_brackets()
    self.lines                        = 0
    self.chars                        = 0
    self.count_lines                  = count_lines
    self.ignore_angle                 = bool(self.settings.get('ignore_non_tags'))
    self.tag_type                     = self.settings.get('tag_type')
    self.show_bracket                 = show

    # Search threshold
    self.adj_only             = adj_only if (adj_only != None) else bool(self.settings.get('match_adjacent_only'))
    self.use_threshold        = False if (override_thresh == True) else bool(self.settings.get('use_search_threshold'))
    self.tag_use_threshold    = False if (override_thresh == True) else bool(self.settings.get('tag_use_search_threshold'))
    self.search_threshold     = int(self.settings.get('search_threshold'))
    self.tag_search_threshold = int(self.settings.get('tag_search_threshold'))

    # Tag special options
    self.brackets_only        = bool(self.settings.get('tag_brackets_only'))

  def init_brackets(self):
    return {
      'bh_curly' : self.get_bracket_settings('curly','{','}'),
      'bh_round' : self.get_bracket_settings('round','(',')'),
      'bh_square': self.get_bracket_settings('square','[',']'),
      'bh_angle' : self.get_bracket_settings('angle','<','>'),
      'bh_tag'   : self.get_bracket_settings('tag','<','>'),
      'bh_quote' : self.get_bracket_settings('quote',"'","'")
    }

  def get_bracket_settings(self, bracket, opening, closing):
    style = sublime.HIDE_ON_MINIMAP 
    if(self.settings.get(bracket+'_style') == "outline"):
      style |= sublime.DRAW_OUTLINED
    elif(self.settings.get(bracket+'_style') == "underline"):
      style |= sublime.DRAW_EMPTY_AS_OVERWRITE
    return {
      'enable'   : bool(self.settings.get(bracket+'_enable')),
      'scope'    : self.settings.get(bracket+'_scope'),
      'style'    : style,
      'underline': (self.settings.get(bracket+'_style') == "underline"),
      'icon'     : self.settings.get(bracket+'_icon'),
      'list'     : map(lambda x:x.lower(),self.settings.get(bracket+'_language_list')),
      'filter'   : self.settings.get(bracket+'_language_filter'),
      'open'     : opening,
      'close'    : closing
    }

  def init_match(self):
    # Current language
    language          = basename(self.view.settings().get('syntax')).replace('.tmLanguage','').lower()
    # Reset objects
    self.sels         = []
    self.targets      = []
    self.highlight_us = {}
    self.lines        = 0
    self.multi_select = False
    self.search_left  = self.search_threshold
    self.adj_bracket  = False
    
    # Standard Brackets
    if (self.exclude_bracket('bh_curly',language) == False): 
      self.add_bracket('bh_curly')
    if (self.exclude_bracket('bh_round',language) == False): 
      self.add_bracket('bh_round')
    if (self.exclude_bracket('bh_square',language) == False): 
       self.add_bracket('bh_square')
    if (self.exclude_bracket('bh_angle',language) == False): 
       self.add_bracket('bh_angle')
    # Tags
    if(self.exclude_bracket('bh_tag',language) == False):
      self.tag_enable = True
      self.highlight_us['bh_tag'] = []
    else:
      self.tag_enable = False
    # Quotes
    if(self.exclude_bracket('bh_quote',language) == False):
      self.quote_enable = True
      self.highlight_us['bh_quote'] = []
    else:
      self.quote_enable = False

  def add_bracket(self,bracket):
    self.highlight_us[bracket] = []
    self.targets.append(bracket)

  def exclude_bracket (self, bracket, language):
    exclude = True
    if(self.brackets[bracket]['enable'] == True):
      # Black list languages
      if(self.brackets[bracket]['filter'] == 'blacklist'):
        exclude      = False
        if(language != None):
          for item in self.brackets[bracket]['list']:
            if(language == item):
              exclude = True
              break;
      #White list languages
      elif(self.brackets[bracket]['filter'] == 'whitelist'):
        if(language != None):
          for item in self.brackets[bracket]['list']:
            if(language == item):
              exclude = False
              break
    return exclude

  def unique(self):
    id_view = self.view.id()
    id_sel  = ''
    is_unique = False
    for sel in self.view.sel():
      id_sel = id_sel + str(sel.a)
    if( id_view != self.last_id_view or id_sel != self.last_id_sel):
      self.last_id_view = id_view
      self.last_id_sel  = id_sel
      is_unique = True
    return is_unique

  def highlight(self, view):
    # Perform highlight on brackets and tags
    for bracket in self.brackets:
      if(bracket in self.highlight_us):
        view.add_regions(
          bracket,
          self.highlight_us[bracket],
          self.brackets[bracket]['scope'],
          self.brackets[bracket]['icon'],
          self.brackets[bracket]['style']
        )
      else:
        view.erase_regions(bracket)

  def store_sel(self,left,right):
    if(self.show_bracket == None):
      return
    if(self.show_bracket == 'left'):
      self.sels.append(left)
    elif(self.show_bracket == 'right'):
      self.sels.append(right)
    elif(self.show_bracket == 'select'):
      self.sels.append(sublime.Region(left,right))

  def go_brackets(self):
    if(self.show_bracket != None and len(self.sels) > 0):
      if (self.multi_select == False):
        self.view.show(self.sels[0])
      self.view.sel().clear()
      map(lambda x: self.view.sel().add(x), self.sels)

  def offset_cursor(self,scout):
    # Offset cursor
    offset = 0
    if (offset == 0):
      char1 = self.view.substr(scout - 1)
      char2 = self.view.substr(scout)
      for bracket in self.targets:
        if(char2 == self.brackets[bracket]['open'] or char1 == self.brackets[bracket]['open']):
          self.adj_bracket = True
        if(char1 == self.brackets[bracket]['close']):
          offset -= 2
          self.adj_bracket = True
          break
        elif(char2 == self.brackets[bracket]['close']):
          offset -= 1
          self.adj_bracket = True
    return offset

  def match(self, view):
    # Setup views
    self.view      = view
    self.window    = view.window()
    self.last_view = view
    self.multi_select = (len(view.sel()) > 1)

    if(self.unique()):
      # Initialize
      self.init_match()
      # Clear views.
      if self.window != None:
        for clear_view in self.window.views():
          self.highlight(clear_view)
      # Process selections.
      for sel in view.sel():
        start = sel.a
        # Match quotes if enabled and within a string
        if(self.quote_enable == True):
          (matched,start) = self.match_quotes(start)
          # Try and match brackets if quotes failed
          if(matched == False):
            self.match_braces(start)
        else:
          self.match_braces(start + self.offset_cursor(start))
    # Highlight.
    self.go_brackets()
    self.highlight(view)
    if(self.count_lines == True):
      sublime.status_message('In Block: Lines '+str(self.lines)+", Chars "+str(self.chars))

  def match_braces(self, sel):
    start = sel
    if(self.adj_only == True):
      if(not self.adj_bracket):
        return

    # Find left brace
    left = self.scout_left(start)
    if(left != None):
      for bracket in self.targets:
        if(self.view.substr(left) == self.brackets[bracket]['open']):
          self.bracket_type  = bracket
          self.bracket_open  = self.brackets[bracket]['open']
          self.bracket_close = self.brackets[bracket]['close']
          break
      # Find right brace
      right = self.scout_right(start+1)
    # Matches found
    if(left != None and right != None):
      # Angle specific
      if(self.bracket_type == 'bh_angle'):
        # Find tags if required
        if( self.tag_enable == True and 
            is_tag(self.view.substr(sublime.Region(left,right+1))) == True):
          if (self.match_tags(left,right)):
            return
        # Continue higlighting angle unless required not to
        if(self.ignore_angle == True):
          self.store_sel(sel,sel)
          return
      # Set higlight regions
      if(self.brackets[self.bracket_type]['underline']):
        self.highlight_us[self.bracket_type].append(sublime.Region(left))
        self.highlight_us[self.bracket_type].append(sublime.Region(right))
      else:
        self.highlight_us[self.bracket_type].append(sublime.Region(left, left + 1))
        self.highlight_us[self.bracket_type].append(sublime.Region(right, right + 1))
      if(self.count_lines == True):
        self.lines += self.view.rowcol(right)[0] - self.view.rowcol(left)[0] + 1
        self.chars += right - 1 - left
      self.store_sel(left + 1, right)
    else:
      self.store_sel(sel,sel)

  def scout_left(self, scout):
    count = {}
    for bracket in self.targets:
      count[bracket] = 0

    while(scout >= 0):
      if (self.use_threshold == True):
        self.search_left -= 1
        if(self.search_left < 0):
          return None
      # Are we in a string or comment?
      if( self.view.score_selector(scout, 'string') == 0 and 
          self.view.score_selector(scout, 'comment')== 0 and
          self.view.score_selector(scout, 'keyword.operator') == 0):
        # Assign char.
        char = self.view.substr(scout)
        # Hit brackets.
        foundBracket = False
        for bracket in self.targets:
          if (char == self.brackets[bracket]['open']):
            if(count[bracket] > 0):
              count[bracket] -= 1
              foundBracket = True
              break
            else:
              return scout

        if(foundBracket == False):
          for bracket in self.targets:
            if (char == self.brackets[bracket]['close']):
              count[bracket] += 1
              break
      scout -= 1

  def scout_right(self, scout):
    brackets = 0

    viewSize = self.view.size()
    while(scout < viewSize):
      if (self.use_threshold == True):
        self.search_left -= 1
        if(self.search_left < 0):
          return None
      # Are we in a string or comment?
      if( self.view.score_selector(scout, 'string') == 0 and
          self.view.score_selector(scout, 'comment') == 0 and
          self.view.score_selector(scout, 'keyword.operator') == 0): 
        # Assign char.
        char = self.view.substr(scout)
        # Hit brackets.
        if(char == self.bracket_close):
          if(brackets > 0):
            brackets -= 1
          else: 
            return scout
        elif(char == self.bracket_open):
          brackets += 1
      scout += 1

  def match_tags(self, start, end):
    self.search_left = self.tag_search_threshold
    blotch = True

    # Go find tags. Limit search with threshold if required
    bufferSize   = self.view.size()
    bufferRegion = sublime.Region(0, bufferSize)
    bufferText   = self.view.substr(bufferRegion)
    curPosition  = start + 1
    foundTags    = match(bufferText, curPosition, self.tag_type, self.tag_use_threshold, self.search_left)

    # Find brackets inside tags
    tag1 = { "match": foundTags[0] }
    tag2 = { "match": foundTags[1] }
    if( str(tag1['match']) != 'None' and 
        self.view.substr(tag1['match'] + 1) != '!' and 
        self.view.substr(tag1['match'] - 1) != '`' and 
        self.view.substr(tag1['match']) == '<' and 
        self.view.substr(curPosition) != '<'):

      # Get 1st Tag
      matched = False
      # Already have end points?
      if(tag1['match'] == start):
        tag1['begin'] = start
        tag1['end']   = end
      # Calculate end points
      else:
        tag1['begin'] = tag1['match']
        tag1['end']   = tag1['match']
        while(self.view.substr(tag1['end']) != '>' or self.view.score_selector(tag1['end'], 'string')):
          tag1['end'] = tag1['end'] + 1
          if( self.view.substr(tag1['end']) == '<' and self.view.score_selector(tag1['end'], 'string') == 0):
            matched = False
      # Create regions to highlight
      if(self.brackets_only == True):
        tag1['region']  = sublime.Region(tag1['begin'], tag1['begin']+1)
        tag1['region2'] = sublime.Region(tag1['end'], tag1['end'] + 1)
      else:
        tag1['region'] = sublime.Region(tag1['begin'], tag1['end'] + 1)

      # Get 2nd Tag
      # Already have end points?
      if(tag2['match'] == end + 1):
         tag2['end']   = end
         tag2['begin'] = start
      # Calculate end points
      else:
        tag2['end']   = tag2['match'] - 1
        tag2['begin'] = tag2['end']
        while(self.view.substr(tag2['begin']) != '<' or self.view.score_selector(tag2['begin'], 'string')):
          tag2['begin'] = tag2['begin'] - 1
      # Create regions to highlight
      if(self.brackets_only == True):
        tag2['region']  = sublime.Region(tag2['begin'], tag2['begin']+1)
        tag2['region2'] = sublime.Region(tag2['end'], tag2['end'] + 1)
      else:
        tag2['region'] = sublime.Region(tag2['begin'], tag2['end'] + 1)

      # Set Highlight Region
      if(matched == True):
        if(self.brackets_only == True):
          self.highlight_us['bh_tag'].append(tag1['region'])
          self.highlight_us['bh_tag'].append(tag1['region2'])
          self.highlight_us['bh_tag'].append(tag2['region'])
          self.highlight_us['bh_tag'].append(tag2['region2'])
        else:
          self.highlight_us['bh_tag'].append(tag1['region'])
          self.highlight_us['bh_tag'].append(tag2['region'])
        if(self.brackets['bh_tag']['underline'] == True):
          self.highlight_us['bh_tag'] = self.underline_tag(self.highlight_us['bh_tag'])
        if(self.count_lines == True):
          self.lines += self.view.rowcol(tag2['begin'])[0] - self.view.rowcol(tag1['end'])[0] + 1
          self.chars += tag2['begin'] - 1 - tag1['end']
        self.store_sel(tag1['end'] + 1, tag2['begin'])
    return not blotch

  def underline_tag(self,regions):
    underline = []
    for region in regions:
      start = region.begin()
      end   = region.end()
      while (start < end):
        underline.append(sublime.Region(start))
        start += 1
    return underline

  def match_quotes(self, start):
    matched = False
    bail    = False
    #Check if likely a string
    left_side_match  = (self.view.score_selector(start, 'string') > 0)
    right_side_match = (self.view.score_selector(start - 1, 'string') > 0)
    if(self.adj_only):
      far_left_side_match  = (self.view.score_selector(start - 2, 'string') > 0)
      far_right_side_match = (self.view.score_selector(start + 1, 'string') > 0)
      bail = not ((left_side_match or right_side_match) and
                  ((left_side_match != right_side_match) or
                  not far_left_side_match or 
                  not far_right_side_match))
    if((left_side_match or right_side_match) and bail == False):
      # Calculate offset
      offset  = -1 if(left_side_match == False) else 0
      (matched,start) = self.find_quotes(start + offset)
    else:
      start += self.offset_cursor(start)
    return (matched,start)

  def find_quotes(self, start):
    begin    = start
    end      = start
    scout    = start
    quote    = None
    lastChar = None
    matched  = False

    # Left quote
    while(scout >= 0):
      if (self.use_threshold == True):
        self.search_left -= 1
        if(self.search_left < 0):
          return (matched, scout)
      char = self.view.substr(scout)
      if( self.view.score_selector(scout, 'string') > 0):
        if(scout == 0):
          begin = scout
          if(char == "'" or char == '"'):
            quote = char
          break
        else:
          scout -= 1
          lastChar = char
      else:
        begin = scout + 1
        if(lastChar == "'" or lastChar == '"'):
          quote = lastChar
        break

    # If quote fails continue off from furthest left
    # to find other brackets
    search_left = self.search_left
    self.search_left += 1

    # Right quote
    if(quote != None):
      scout = start
      viewSize = self.view.size() - 1
      lastChar = None
      while(scout <= viewSize):
        if (self.use_threshold == True):
          search_left -= 1
          if(search_left < 0):
            return (matched, begin-1)
        char = self.view.substr(scout)
        if( self.view.score_selector(scout, 'string') > 0):
          if(scout == viewSize):
            if(char == quote and scout != begin):
              end = scout + 1
              matched = True
            break
          else:
            scout += 1
            lastChar = char
        else:
          if(lastChar == quote and scout - 1 != begin):
            end = scout
            matched = True
          break

    if(matched == True):
      if(self.brackets['bh_quote']['underline'] == True):
        self.highlight_us['bh_quote'].append(sublime.Region(begin))
        self.highlight_us['bh_quote'].append(sublime.Region(end-1))
      else:
        self.highlight_us['bh_quote'].append(sublime.Region(begin, begin+1))
        self.highlight_us['bh_quote'].append(sublime.Region(end-1, end))
      if(self.count_lines == True):
        self.lines += self.view.rowcol(end)[0] - self.view.rowcol(begin)[0] + 1
        self.chars += end - 2 - begin
      self.store_sel(begin+1, end-1)
    return (matched, begin-1)

  def on_load(self, view):
    self.match(view)

  def on_modified(self, view):
    # Force unique view in order to update in all changes
    self.last_id_view = None
    # Start matching
    self.match(view)

  def on_activated(self,view):
    self.match(view)

  def on_selection_modified(self, view):
    #global bracket_modified_event_fired
    self.match(view)
