import sublime, sublime_plugin

class SublimeBracketsKeyCommand(sublime_plugin.WindowCommand):
  def run(self):
    SublimeBracketsCommand().on_selection_modified(self.window.active_view(),True)

class SublimeBracketsCommand(sublime_plugin.EventListener):
  #Initialize
  Settings = sublime.load_settings('SublimeBrackets.sublime-settings')
  UseThreshold = None
  Targets = None
  highlight_us = None
  SearchThreshold = None
  view = None
  window = None
  last_id_view = None
  last_id_sel = None

  def on_selection_modified(self, view, overrideThresh=False):
    #setup views
    self.view = view
    self.window = view.window()
    self.last_view = view

    if(self.unique()):
      #init
      self.init(overrideThresh)
      # Clear views.
      if self.window != None:
        for clear_view in self.window.views():
          self.highlight(clear_view)
      # Process selections.
      for sel in view.sel():
        self.match_braces(sel)
    # Highlight.
    self.highlight(view)

  def init(self,overrideThresh):
    self.Targets = {}
    self.highlight_us = {}
    self.addBracket('curly','{','}')
    self.addBracket('round','(',')')
    self.addBracket('square','[',']')
    self.addBracket('angle','<','>')
    self.SearchThreshold = int(self.Settings.get('search_threshold'))
    if(overrideThresh == True):
      self.UseThreshold = False
    else:
      self.UseThreshold = bool(self.Settings.get('use_search_threshold'))


  def addBracket(self, bracket, opening, closing):
    if(bool(self.Settings.get(bracket+'_enable')) == True):
      self.Targets[bracket] = {
        'scope' : self.Settings.get(bracket+'_scope'),
        'outline' : bool(self.Settings.get(bracket+'_outline')),
        'icon' : self.Settings.get(bracket+'_icon'),
        'open' : opening,
        'close' : closing
      }
      self.highlight_us[bracket] = []

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
    for bracket in self.Targets:
      if(self.Targets[bracket]['outline'] == True):
        view.add_regions(
          bracket,
          self.highlight_us[bracket],
          self.Targets[bracket]['scope'],
          self.Targets[bracket]['icon'],
          sublime.DRAW_OUTLINED
        )
      elif(self.Targets[bracket]['outline'] == False):
        view.add_regions(
          bracket, 
          self.highlight_us[bracket], 
          self.Targets[bracket]['scope'],
          self.Targets[bracket]['icon'],
          sublime.HIDE_ON_MINIMAP
        )

  def match_braces(self, sel):
    left = self.scout_left(sel.a + self.checkOffset(sel.a))
    if(left != None):
      for bracket in self.Targets:
        if(self.view.substr(left) == self.Targets[bracket]['open']):
          self.bracket_type = bracket
          self.bracket_open = self.Targets[bracket]['open']
          self.bracket_close = self.Targets[bracket]['close']
          break
      right = self.scout_right(left + 1)
    if(left != None and right != None):
      region = sublime.Region(left, left + 1)
      self.highlight_us[self.bracket_type].append(region)
      region = sublime.Region(right, right + 1)
      self.highlight_us[self.bracket_type].append(region)

  def checkOffset(self,scout):
    offset = 0
    if (offset == 0):
      char = self.view.substr(scout - 1)
      for bracket in self.Targets:
        if(char == self.Targets[bracket]['close']):
          offset -= 2
    if (offset == 0):
      char = self.view.substr(scout)
      for bracket in self.Targets:
        if(char == self.Targets[bracket]['close']):
          offset -= 1

    return offset

  def scout_left(self, scout):
    brackets = {}
    for bracket in self.Targets:
      brackets[bracket] = {
        'count' : 0,
        'open' : self.Targets[bracket]['open'],
        'close' : self.Targets[bracket]['close'],
      }

    while(scout > 0):
      if (self.UseThreshold == True):
        self.SearchThreshold -= 1
        if(self.SearchThreshold < 0):
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
      if (self.UseThreshold == True):
        self.SearchThreshold -= 1
        if(self.SearchThreshold < 0):
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
