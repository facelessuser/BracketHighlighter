import sublime, sublime_plugin

class MatchCommand(sublime_plugin.EventListener):

  # Customize
  #--------------------
  # Scope? (Defined in theme files.) ->
  # Examples: (keyword/string/number)
  CurlyScope = 'entity.name.class'
  RoundScope = 'entity.name.class'
  SquareScope = 'entity.name.class'
  # Outline? (True/False) ->
  CurlyOutline = True
  RoundOutline = True
  SquareOutline = True
  # Icon? (dot/circle/bookmark/cross)
  CurlyIcon = 'dot'
  RoundIcon = 'dot'
  SquareIcon = 'dot'
  #--------------------
  # End Customize

  view = None
  window = None
  highlight_us = None
  last_id_view = None
  last_id_sel = None

  def on_selection_modified(self, view):
    self.view = view
    self.window = view.window()
    self.last_view = view

    if(self.unique()):
      # Clear views.
      self.highlight_us = {
        'curly': [],
        'round': [],
        'square': []
      }
      for clear_view in self.window.views():
        self.highlight(clear_view)
      # Process selections.
      for sel in view.sel():
        self.match_braces(sel)
    # Highlight.
    self.highlight(view)

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

  def highlight(self, view):

    # Curly Highlight.
    if(self.CurlyOutline == True):
      view.add_regions(
        'curly', 
        self.highlight_us['curly'], 
        self.CurlyScope,
        self.CurlyIcon,
        sublime.DRAW_OUTLINED
      )
    elif(self.CurlyOutline == False):
      view.add_regions(
        'curly', 
        self.highlight_us['curly'], 
        self.CurlyScope,
        self.CurlyIcon,
        sublime.HIDE_ON_MINIMAP
      )

    # Round Highlight.
    if(self.RoundOutline == True):
      view.add_regions(
        'round', 
        self.highlight_us['round'], 
        self.RoundScope,
        self.RoundIcon,
        sublime.DRAW_OUTLINED
      )
    elif(self.RoundOutline == False):
      view.add_regions(
        'round', 
        self.highlight_us['round'], 
        self.RoundScope,
        self.RoundIcon,
        sublime.HIDE_ON_MINIMAP
      )

    # Square Highlight.
    if(self.SquareOutline == True):
      view.add_regions(
        'square', 
        self.highlight_us['square'], 
        self.SquareScope,
        self.SquareIcon,
        sublime.DRAW_OUTLINED
      )
    elif(self.SquareOutline == False):
      view.add_regions(
        'square', 
        self.highlight_us['square'], 
        self.SquareScope,
        self.SquareIcon,
        sublime.HIDE_ON_MINIMAP
      )

  def match_braces(self, sel):
    self.bracket_type = None
    left = self.scout_left(sel.a)
    if(left != None):
      right = self.scout_right(left + 1)
    if(left != None and right != None):
      if(self.view.substr(left) == '{'):
        bracket_type = 'curly'
      if(self.view.substr(left) == '('):
        bracket_type = 'round'
      if(self.view.substr(left) == '['):
        bracket_type = 'square'
      region = sublime.Region(left, left + 1)
      self.highlight_us[bracket_type].append(region)
      region = sublime.Region(right, right + 1)
      self.highlight_us[bracket_type].append(region)

  def scout_left(self, scout):
    brackets = {
      'curly': 0,
      'round': 0,
      'square': 0,
    }
    a_check = True
    b_check = True
    scout = scout + 1
    while(scout > 0):
      scout = scout - 1
      # Cicumstance checks.
      if(a_check == True):
        a_check = False
        char = self.view.substr(scout - 1)
        if( char == '}' or
            char == ')' or
            char == ']'):
          continue
      if(b_check == True):
        b_check = False
        char = self.view.substr(scout)
        if( char == '}' or
            char == ')' or
            char == ']'):
          continue
      # Are we in a string?
      if( self.view.score_selector(scout, 'string') > 0 or
          self.view.score_selector(scout, 'comment') > 0): 
        continue
      # Assign char.
      char = self.view.substr(scout)
      # Hit start bracket
      if(char == '{'):
        if(brackets['curly'] > 0):
          brackets['curly'] = brackets['curly'] - 1
        else: 
          self.bracket_type = 'curly'
          return scout
      elif(char == '('):
        if(brackets['round'] > 0):
          brackets['round'] = brackets['round'] - 1
        else: 
          self.bracket_type = 'round'
          return scout
      elif(char == '['):
        if(brackets['square'] > 0):
          brackets['square'] = brackets['square'] - 1
        else: 
          self.bracket_type = 'square'
          return scout
      elif(char == '}'):
        brackets['curly'] = brackets['curly'] + 1
      elif(char == ')'):
        brackets['round'] = brackets['round'] + 1
      elif(char == ']'):
        brackets['square'] = brackets['square'] + 1

  def scout_right(self, scout):
    brackets = {
      'curly': 0,
      'round': 0,
      'square': 0,
    }
    scout = scout - 1
    while(scout < self.view.size()):
      scout = scout + 1
      # Are we in a string?
      if( self.view.score_selector(scout, 'string') > 0 or
          self.view.score_selector(scout, 'comment') > 0): 
        continue
      # Assign char.
      char = self.view.substr(scout)
      # Hit start bracket
      if(char == '}'):
        if(brackets['curly'] > 0):
          brackets['curly'] = brackets['curly'] - 1
        else: 
          self.bracket_type = 'curly'
          return scout
      elif(char == ')'):
        if(brackets['round'] > 0):
          brackets['round'] = brackets['round'] - 1
        else: 
          self.bracket_type = 'round'
          return scout
      elif(char == ']'):
        if(brackets['square'] > 0):
          brackets['square'] = brackets['square'] - 1
        else: 
          self.bracket_type = 'square'
          return scout
      elif(char == '{'):
        brackets['curly'] = brackets['curly'] + 1
      elif(char == '('):
        brackets['round'] = brackets['round'] + 1
      elif(char == '['):
        brackets['square'] = brackets['square'] + 1