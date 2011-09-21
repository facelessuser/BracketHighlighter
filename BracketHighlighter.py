from os.path import basename
from Elements import is_tag, match
import sublime, sublime_plugin

class BracketHighlighterKeyCommand(sublime_plugin.WindowCommand):
    def run(self):
      BracketHighlighterCommand(True,True).match(self.window.active_view())

class BracketHighlighterCommand(sublime_plugin.EventListener):
  # Initialize
  def __init__(self, override_thresh=False, count_lines=False):
    self.settings = sublime.load_settings('BracketHighlighter.sublime-settings')
    self.settings.add_on_change('reload', lambda: self.setup())
    self.setup(override_thresh,count_lines)

  def setup(self,override_thresh=False, count_lines=False):
    self.bracket_modified_event_fired = False
    self.last_id_view                 = None
    self.last_id_sel                  = None
    self.targets                      = {}
    self.highlight_us                 = {}
    self.brackets                     = self.initBrackets()
    self.lines                        = 0
    self.count_lines                  = count_lines

    # Search threshold
    self.use_threshold        = False if (override_thresh == True) else bool(self.settings.get('use_search_threshold'))
    self.tag_use_threshold    = False if (override_thresh == True) else bool(self.settings.get('tag_use_search_threshold'))
    self.search_threshold     = int(self.settings.get('search_threshold'))
    self.tag_search_threshold = int(self.settings.get('tag_search_threshold'))

    # Tag special options
    self.brackets_only        = bool(self.settings.get('tag_brackets_only'))

  def initBrackets(self):
    return {
      'curly' : self.get_bracket_settings('curly','{','}'),
      'round' : self.get_bracket_settings('round','(',')'),
      'square': self.get_bracket_settings('square','[',']'),
      'angle' : self.get_bracket_settings('angle','<','>'),
      'tag'   : self.get_bracket_settings('tag','<','>'),
      'quote' : self.get_bracket_settings('quote',"'","'")
    }

  def get_bracket_settings(self, bracket, opening, closing):
    return {
      'enable'  : bool(self.settings.get(bracket+'_enable')),
      'scope'   : self.settings.get(bracket+'_scope'),
      'outline' : (sublime.DRAW_OUTLINED if (bool(self.settings.get(bracket+'_outline'))) else sublime.HIDE_ON_MINIMAP),
      'icon'    : self.settings.get(bracket+'_icon'),
      'exclude' : str(self.settings.get(bracket+'_exclude_language')).lower().split(','),
      'open'    : opening,
      'close'   : closing
    }

  def init(self):
    # Current language
    language          = basename(self.view.settings().get('syntax')).replace('.tmLanguage','').lower()
    # Reset objects
    self.targets      = {}
    self.highlight_us = {}
    self.lines        = 0
    
    # Standard Brackets
    if (self.exclude_bracket('curly',language) == False): 
      self.add_bracket('curly')
    if (self.exclude_bracket('round',language) == False): 
      self.add_bracket('round')
    if (self.exclude_bracket('square',language) == False): 
       self.add_bracket('square')
    if (self.exclude_bracket('angle',language) == False): 
       self.add_bracket('angle')
    # Tags
    self.tag_enable   = (self.exclude_bracket('tag',language) == False)
    self.highlight_us['tag'] = []
    # Quotes
    self.quote_enable = (self.exclude_bracket('quote',language) == False)
    self.highlight_us['quote'] = []

  def add_bracket(self,bracket):
    self.highlight_us[bracket] = []
    self.targets[bracket] = self.brackets[bracket]

  def exclude_bracket (self, bracket, language):
    exclude = True
    if(self.brackets[bracket]['enable'] == True):
      exclude      = False
      if(language != None):
        for item in self.brackets[bracket]['exclude']:
          if(language == item):
            exclude = True
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

  def on_modified(self, view):
    # Keep selection method from firing
    self.bracket_modified_event_fired = True
    # Force unique view in order to update in all changes
    self.last_id_view = None
    # Start matching
    self.match(view)

  def on_selection_modified(self, view):
    #global bracket_modified_event_fired
    if(self.bracket_modified_event_fired == True):
      self.bracket_modified_event_fired = False
      return
    # Start matching
    self.match(view)

  def match(self, view):
    # Setup views
    self.view      = view
    self.window    = view.window()
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
    if(self.count_lines == True):
      sublime.status_message('Lines in Block '+str(self.lines))

  def highlight(self, view):

    # Perform highlight on brackets and tags
    for bracket in self.targets:
      view.add_regions(
        bracket,
        self.highlight_us[bracket],
        self.targets[bracket]['scope'],
        self.targets[bracket]['icon'],
        self.targets[bracket]['outline']
      )
    # Highlight tags
    view.add_regions(
      'tag',
      self.highlight_us['tag'],
      self.brackets['tag']['scope'],
      self.brackets['tag']['icon'],
      self.brackets['tag']['outline']
    )
    # Highlight quotes
    view.add_regions(
      'quote',
      self.highlight_us['quote'],
      self.brackets['quote']['scope'],
      self.brackets['quote']['icon'],
      self.brackets['quote']['outline']
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
    offset           = self.offset_cursor(sel)
    start            = sel + offset

    # Find left brace
    left = self.scout_left(start)
    if(left != None):
      for bracket in self.targets:
        if(self.view.substr(left) == self.targets[bracket]['open']):
          self.bracket_type  = bracket
          self.bracket_open  = self.targets[bracket]['open']
          self.bracket_close = self.targets[bracket]['close']
          break
      # Find right brace
      right = self.scout_right(start+1)
    # Matches found
    if(left != None and right != None):
      # Angle specific
      if(self.bracket_type == 'angle'):
        # Find tags if required
        if( self.tag_enable == True and 
            is_tag(self.view.substr(sublime.Region(left,right+1))) == True):
          if (self.match_tags(left,right)):
            return
        # Continue higlighting angle unless required not to
        if(bool(self.settings.get('ignore_non_tags')) == True):
          return
      # Set higlight regions
      region = sublime.Region(left, left + 1)
      self.highlight_us[self.bracket_type].append(region)
      region = sublime.Region(right, right + 1)
      self.highlight_us[self.bracket_type].append(region)
      if(self.count_lines == True):
        self.lines = self.view.rowcol(right)[0] - self.view.rowcol(left)[0] + 1

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

  def match_tags(self, start, end):
    self.search_left = self.tag_search_threshold
    blotch = True

    # Go find tags. Limit search with threshold if required
    bufferSize   = self.view.size()
    bufferRegion = sublime.Region(0, bufferSize)
    bufferText   = self.view.substr(bufferRegion)
    curPosition  = start + 1
    foundTags    = match(bufferText, curPosition, self.settings.get('tag_type'), self.tag_use_threshold, self.search_left)

    # Find brackets inside tags
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
        tag1['end']   = end
      # Calculate end points
      else:
        tag1['begin'] = tag1['match']
        tag1['end']   = tag1['match']
        while(self.view.substr(tag1['end']) != '>' or self.view.score_selector(tag1['end'], 'string')):
          tag1['end'] = tag1['end'] + 1
          if( self.view.substr(tag1['end']) == '<' and self.view.score_selector(tag1['end'], 'string') == 0):
            blotch = True
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
      if(blotch == False):
        if(self.brackets_only == True):
          self.highlight_us['tag'].append(tag1['region'])
          self.highlight_us['tag'].append(tag1['region2'])
          self.highlight_us['tag'].append(tag2['region'])
          self.highlight_us['tag'].append(tag2['region2'])
        else:
          self.highlight_us['tag'].append(tag1['region'])
          self.highlight_us['tag'].append(tag2['region'])
        if(self.count_lines == True):
          self.lines = self.view.rowcol(tag2['begin'])[0] - self.view.rowcol(tag1['end'])[0] + 1
    return not blotch

  def match_quotes(self, start):
    matched = False
    if(self.quote_enable == False):
      return matched
    self.search_left = self.search_threshold
    left_side_match  = (self.view.score_selector(start, 'string') > 0)
    right_side_match = (self.view.score_selector(start - 1, 'string') > 0)
    if( start > 0 and (left_side_match or right_side_match)):
      # Calculate offset
      offset  = -1 if(left_side_match == False) else 0
      matched = self.find_quotes(start + offset)
    return matched

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
          if(lastChar == quote and scout - 1 != begin):
            end = scout
            matched = True
          break

    if(matched == True):
      self.highlight_us['quote'].append(sublime.Region(begin, begin+1))
      self.highlight_us['quote'].append(sublime.Region(end - 1, end))
      if(self.count_lines == True):
        self.lines = self.view.rowcol(begin)[0] - self.view.rowcol(end)[0] + 1
    return matched
