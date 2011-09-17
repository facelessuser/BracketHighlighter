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
    self.view = view
    self.window = view.window()
    self.last_view = view

    if(self.unique()):
      # Clear views.
      self.init()
      if(overrideThresh == True):
        self.UseThreshold = False

      if self.window != None:
        for clear_view in self.window.views():
          self.highlight(clear_view)
      # Process selections.
      for sel in view.sel():
        self.match_braces(sel)
    # Highlight.
    self.highlight(view)

  def init(self):
    self.SearchThreshold = int(self.Settings.get('search_threshold'))
    self.UseThreshold = bool(self.Settings.get('use_search_threshold'))
    self.Targets = {}
    self.highlight_us = {}
    self.addBracket('curly','{','}')
    self.addBracket('round','(',')')
    self.addBracket('square','[',']')
    self.addBracket('angle','<','>')

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
    left = self.scout_left(sel.a)
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

  def scout_left(self, scout):
    brackets = {}
    for bracket in self.Targets:
      brackets[bracket] = {
        'count' : 0,
        'open' : self.Targets[bracket]['open'],
        'close' : self.Targets[bracket]['close'],
      }

    a_check = True
    b_check = True
    scout += 1
    max_search = 0
    while(scout > 0):
      max_search += 1
      if (self.UseThreshold == True and max_search >= self.SearchThreshold):
        return None
      scout -= 1
      # Cicumstance checks.
      next = False
      if(a_check == True):
        a_check = False
        char = self.view.substr(scout - 1)
        for bracket in brackets:
          if(char == brackets[bracket]['close']):
            next = True
            break

      if(next == True):
        continue

      if(b_check == True):
        b_check = False
        char = self.view.substr(scout)
        for bracket in brackets:
          if(char == brackets[bracket]['close']):
            next = True
            break

      if(next == True):
        continue

      # Are we in a string?
      if( self.view.score_selector(scout, 'string') > 0 or
          self.view.score_selector(scout, 'comment') > 0): 
        continue
      # Assign char.
      char = self.view.substr(scout)
      # Hit brackets.
      for bracket in brackets:
        if (char == brackets[bracket]['open']):
          if(brackets[bracket]['count'] > 0):
            brackets[bracket]['count'] -= 1
            next == True
            break
          else:
            return scout

      if(next == True):
        continue

      for bracket in brackets:
        if (char == brackets[bracket]['close']):
          brackets[bracket]['count'] += 1
          break

  def scout_right(self, scout):
    brackets = {
      'parentheses': 0
    }
    scout -= 1
    max_search = 0
    while(scout < self.view.size()):
      max_search += 1
      if (self.UseThreshold == True and max_search >= self.SearchThreshold):
        return None
      scout += 1
      # Are we in a string?
      if( self.view.score_selector(scout, 'string') > 0 or
          self.view.score_selector(scout, 'comment') > 0): 
        continue
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
