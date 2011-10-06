import sublime
class select_bracket():
  def run(self, bracket_start, bracket_end, content_start, content_end, select):
    (first,last) = (content_start, content_end)
    if(select == 'left'):
      last = content_start
    elif(select == 'right'):
      first = content_end
    return (bracket_start, bracket_end, content_start, content_end, first, last)