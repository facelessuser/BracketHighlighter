import sublime, sublime_plugin, Elements, os.path

class BracketHighlighterKeyCommand(sublime_plugin.WindowCommand):
    def run(self):
      BracketHighlighterCommand(True).match(self.window.active_view())

class BracketHighlighterCommand(sublime_plugin.EventListener):

  # Initialize
  def __init__(self, overrideThresh=False):
    self.settings = sublime.load_settings('BracketHighlighter.sublime-settings')
    self.bracket_modified_event_fired = False
    self.use_threshold = None
    self.highlight_tags = None
    self.brackets_only = None
    self.targets = None
    self.highlight_us = None
    self.search_threshold = None
    self.search_left = None
    self.view = None
    self.window = None
    self.last_id_view = None
    self.last_id_sel = None
    self.quote_enable = None
    self.bracket_close = None
    self.bracket_open = None

    # Search threshold
    if(overrideThresh == True):
      self.use_threshold = False
    else:
      self.use_threshold = bool(self.settings.get('use_search_threshold'))

    # Tag special options
    self.brackets_only = bool(self.settings.get('tag_brackets_only'))

  def init(self):
    # Current language
    language = os.path.basename(self.view.settings().get('syntax'))
    # Reset objects
    self.targets = {}
    self.highlight_us = {}
    # Standard Brackets
    self.addBracket('curly','{','}',language)
    self.addBracket('round','(',')',language)
    self.addBracket('square','[',']',language)
    self.addBracket('angle','<','>',language)
    # Tags
    if(bool(self.settings.get('tag_enable')) == True and self.exclude_language('tag',language) == False):
      self.highlight_tags = True
    else:
      self.highlight_tags = False
    # Quotes
    if(bool(self.settings.get('quote_enable')) == True and self.exclude_language('quote',language) == False):
      self.quote_enable = True
    else:
      self.quote_enable = False
    self.highlight_us['quote'] = []

    self.search_threshold = int(self.settings.get('search_threshold'))
  
  def addBracket(self, bracket, opening, closing, language):
    if(self.exclude_language(bracket,language) == True):
      return
    if(bool(self.settings.get(bracket+'_enable')) == True):
      self.targets[bracket] = {
        'scope' : self.settings.get(bracket+'_scope'),
        'outline' : bool(self.settings.get(bracket+'_outline')),
        'icon' : self.settings.get(bracket+'_icon'),
        'open' : opening,
        'close' : closing
      }
      self.highlight_us[bracket] = []

  def exclude_language (self, bracket, language):
    exclude = False
    exclude_list = str(self.settings.get(bracket+'_exclude_language')).split(',')
    if(language != None):
      for item in exclude_list:
        if(language == item+".tmLanguage"):
          exclude = True
    return exclude

  def unique(self):
    id_view = self.view.id()
    id_sel = ''
    for sel in self.view.sel():
      id_sel = id_sel + str(sel.a)
    if( id_view != self.last_id_view or
        id_sel != self.last_id_sel):
      self.last_id_view = id_view
      self.last_id_sel = id_sel
      return True
    else:
      return False

  def on_modified(self, view):
    # Delete chars doesn't change the slection
    # But it does register a on_modified event with a selection change
    # Update highlighting here, but keep the on_selection_modified from firing
    #global bracket_modified_event_fired
    self.bracket_modified_event_fired = True
    BracketHighlighterCommand().match(view)

  def on_selection_modified(self, view):
    #global bracket_modified_event_fired
    if(self.bracket_modified_event_fired == True):
      self.bracket_modified_event_fired = False
      return
    self.match(view)

  def match(self, view):
    # Setup views
    self.view = view
    self.window = view.window()
    self.last_view = view

    if(self.unique()):
      # Initialize
      self.init()
      # Clear views.
      if self.window != None:
        for clear_view in self.window.views():
          self.highlight(clear_view)
      # Process selections.
      for sel in view.sel():
        # Match quotes if enabled and within a string
        matched = self.match_quotes(sel.a)

        if(matched == False):
          self.match_braces(sel.a)
    # Highlight.
    self.highlight(view)

  def highlight(self, view):
    # Perform highlight
    highlightStyle = None
    for bracket in self.targets:
      if(self.targets[bracket]['outline'] == True):
        highlightStyle = sublime.DRAW_OUTLINED
      else:
        highlightStyle = sublime.HIDE_ON_MINIMAP
      view.add_regions(
        bracket,
        self.highlight_us[bracket],
        self.targets[bracket]['scope'],
        self.targets[bracket]['icon'],
        highlightStyle
      )
    if(bool(self.settings.get('quote_outline')) == True):
      highlightStyle = sublime.DRAW_OUTLINED
    else:
      highlightStyle = sublime.HIDE_ON_MINIMAP
    view.add_regions(
      'quote',
      self.highlight_us['quote'],
      self.settings.get('quote_scope'),
      self.settings.get('quote_icon'),
      highlightStyle
    )

  def offset_cursor(self,scout):
    # Offset cursor
    offset = 0
    if (offset == 0):
      char1 = self.view.substr(scout - 1)
      char2 = self.view.substr(scout)
      for bracket in self.targets:
        if(char1 == self.targets[bracket]['close']):
          offset -= 2
        elif(char2 == self.targets[bracket]['close']):
          offset -= 1
    return offset

  def match_braces(self, sel):
    self.search_left = self.search_threshold
    offset = self.offset_cursor(sel)
    start = sel + offset

    # Find left brace
    left = self.scout_left(start)
    if(left != None):
      for bracket in self.targets:
        if(self.view.substr(left) == self.targets[bracket]['open']):
          self.bracket_type = bracket
          self.bracket_open = self.targets[bracket]['open']
          self.bracket_close = self.targets[bracket]['close']
          break
      # Find right brace
      right = self.scout_right(start+1)
    # Matches found
    if(left != None and right != None):
      # Angle specific
      if(self.bracket_type == 'angle'):
        # Find tags if required
        if( self.highlight_tags == True and 
            Elements.is_tag(self.view.substr(sublime.Region(left,right+1))) == True):
          if (self.find_tags(left,right)):
            return
        # Continue higlighting angle unless required not to
        if(bool(self.settings.get('ignore_non_tags')) == True):
          return
      # Set higlight regions
      region = sublime.Region(left, left + 1)
      self.highlight_us[self.bracket_type].append(region)
      region = sublime.Region(right, right + 1)
      self.highlight_us[self.bracket_type].append(region)

  def scout_left(self, scout):
    brackets = {}
    for bracket in self.targets:
      brackets[bracket] = {
        'count' : 0,
        'open' : self.targets[bracket]['open'],
        'close' : self.targets[bracket]['close'],
      }

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
        for bracket in brackets:
          if (char == brackets[bracket]['open']):
            if(brackets[bracket]['count'] > 0):
              brackets[bracket]['count'] -= 1
              foundBracket = True
              break
            else:
              return scout

        if(foundBracket == False):
          for bracket in brackets:
            if (char == brackets[bracket]['close']):
              brackets[bracket]['count'] += 1
              break
      scout -= 1

  def scout_right(self, scout):
    brackets = {
      'parentheses': 0
    }
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
          if(brackets['parentheses'] > 0):
            brackets['parentheses'] -= 1
          else: 
            return scout
        elif(char == self.bracket_open):
          brackets['parentheses'] += 1
      scout += 1

  def find_tags(self, start, end):
    self.search_left = self.search_threshold
    blotch = True

    bufferSize = self.view.size()
    bufferRegion = sublime.Region(0, bufferSize)
    bufferText = self.view.substr(bufferRegion)
    curPosition = start + 1
    #Go find tags. Limit search with threshold if required
    foundTags = Elements.match(bufferText, curPosition, self.settings.get('tag_type'), self.use_threshold, self.search_left)
    tag1 = { "match": foundTags[0] }
    tag2 = { "match": foundTags[1] }
    if( str(tag1['match']) != 'None' and 
        self.view.substr(tag1['match'] + 1) != '!' and 
        self.view.substr(tag1['match'] - 1) != '`' and 
        self.view.substr(tag1['match']) == '<' and 
        self.view.substr(curPosition) != '<'):

      # Get 1st Tag
      blotch = False
      # Already have end points?
      if(tag1['match'] == start):
        tag1['begin'] = start
        tag1['end'] = end
      # Calculate end points
      else:
        tag1['begin'] = tag1['match']
        tag1['end'] = tag1['match']
        while(self.view.substr(tag1['end']) != '>' or self.view.score_selector(tag1['end'], 'string')):
          tag1['end'] = tag1['end'] + 1
          if( self.view.substr(tag1['end']) == '<' and self.view.score_selector(tag1['end'], 'string') == 0):
            blotch = True
      # Create regions to highlight
      if(self.brackets_only == True):
        tag1['region'] = sublime.Region(tag1['begin'], tag1['begin']+1)
        tag1['region2'] = sublime.Region(tag1['end'], tag1['end'] + 1)
      else:
        tag1['region'] = sublime.Region(tag1['begin'], tag1['end'] + 1)

      # Get 2nd Tag
      # Already have end points?
      if(tag2['match'] == end + 1):
         tag2['end'] = end
         tag2['begin'] = start
      # Calculate end points
      else:
        tag2['end'] = tag2['match'] - 1
        tag2['begin'] = tag2['end']
        while(self.view.substr(tag2['begin']) != '<' or self.view.score_selector(tag2['begin'], 'string')):
          tag2['begin'] = tag2['begin'] - 1
      # Create regions to highlight
      if(self.brackets_only == True):
        tag2['region'] = sublime.Region(tag2['begin'], tag2['begin']+1)
        tag2['region2'] = sublime.Region(tag2['end'], tag2['end'] + 1)
      else:
        tag2['region'] = sublime.Region(tag2['begin'], tag2['end'] + 1)

      # Set Highlight Region
      if(blotch == False):
        self.targets['angle']['scope'] = self.settings.get('tag_scope')
        self.targets['angle']['icon']  = self.settings.get('tag_icon')
        self.targets['angle']['outline'] = bool(self.settings.get('tag_outline'))
        if(self.brackets_only == True):
          self.highlight_us['angle'].append(tag1['region'])
          self.highlight_us['angle'].append(tag1['region2'])
          self.highlight_us['angle'].append(tag2['region'])
          self.highlight_us['angle'].append(tag2['region2'])
        else:
          self.highlight_us['angle'].append(tag1['region'])
          self.highlight_us['angle'].append(tag2['region'])
    return not blotch

  def match_quotes(self, start):
    matched = False
    self.search_left = self.search_threshold
    is_string = (self.view.score_selector(start, 'string') >= 0)
    if( self.quote_enable == True and
        start > 0 and 
        (is_string or
        self.view.score_selector(start - 1, 'string') > 0)):
      # Calculate offset
      offset = 0
      if(is_string == False):
        offset -= 1
      matched = self.get_quotes(start + offset)
    return matched

  def get_quotes(self, start):
    begin = start
    end = start
    scout = start
    quote = None
    lastChar = None
    matched = False

    # Left quote
    while(scout >= 0):
      if (self.use_threshold == True):
        self.search_left -= 1
        if(self.search_left < 0):
          return None
      char = self.view.substr(scout)
      if( self.view.score_selector(scout, 'string') > 0):
        if(scout == 0 and (char == "'" or char == '"')):
          quote = char
          begin = scout
          break
        else:
          scout -= 1
          lastChar = char
      else:
        begin = scout + 1
        quote = lastChar
        break

    # Right quote
    if(quote != None):
      scout = start
      viewSize = self.view.size() - 1
      lastChar = None
      while(scout <= viewSize):
        if (self.use_threshold == True):
          self.search_left -= 1
          if(self.search_left < 0):
            return None
        char = self.view.substr(scout)
        if( self.view.score_selector(scout, 'string') > 0):
          if(scout == viewSize and char == quote and scout != begin):
            end = scout + 1
            matched = True
            break
          else:
            scout += 1
            lastChar = char
        else:
          if(lastChar == quote and scout != begin - 1):
            end = scout
            matched = True
          break

    if(matched == True):
      self.highlight_us['quote'].append(sublime.Region(begin, begin+1))
      self.highlight_us['quote'].append(sublime.Region(end - 1, end))
    return matched
