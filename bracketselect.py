import bracket_plugin
import sublime
class select_bracket(bracket_plugin.BracketPluginCommand):
  def run(self, bracket, content, selection, select=''):
    (first,last) = (content.a, content.b)
    if(select == 'left'):
      last = content.a
    elif(select == 'right'):
      first = content.b
    return (bracket, content, [sublime.Region(first, last)])
