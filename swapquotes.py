import sublime
class swap_quotes():
  def escaped(self, idx, view):
    escaped = False
    while (idx >= 0 and view.substr(idx) == '\\'):
      escaped = ~escaped
      idx -= 1
    return escaped

  def run(self, bracket_start, bracket_end, content_start, content_end):
    view  = sublime.active_window().active_view()
    quote = view.substr(bracket_start)
    begin = bracket_start + 1
    new   = "'" if (quote == '"') else '"'
    old   = '"' if (quote == '"') else "'"
    edit  = view.begin_edit();
    while (begin < bracket_end):
      char = view.substr(begin)
      if( char == old and self.escaped(begin -1, view)):
        view.replace(edit, sublime.Region(begin - 1, begin), '')
        bracket_end -= 1
        content_end -= 1
      elif(char == new and not self.escaped(begin -1, view)):
        view.insert(edit, begin, '\\')
        bracket_end += 1
        content_end += 1
      begin += 1
    view.replace(edit, sublime.Region(bracket_start , bracket_start+1), new)
    view.replace(edit, sublime.Region(bracket_end - 1, bracket_end), new)
    view.end_edit(edit)
    return (bracket_start, bracket_end, content_start, content_end)
