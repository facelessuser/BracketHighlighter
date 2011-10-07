import sublime
class BracketPlugin():
  def __init__(self, plugin):
    self.enabled = False
    self.args = plugin['args'] if ("args" in plugin) else {}
    self.plugin = None
    if('command' in plugin):
      try:
        (module_name,class_name) = plugin['command'].split('.')
        module   = __import__(module_name)
        self.plugin = getattr(module, class_name)
        self.enabled = True
      except Exception:
        sublime.error_message('Can not load plugin: '+plugin['command'])

  def is_enabled(self):
    return self.enabled

  def run_command(self,bracket, content, selection):
    self.args['bracket']   = bracket
    self.args['content']   = content
    self.args['selection'] = selection
    return self.plugin().run(**self.args)

class BracketPluginCommand():
  def __init__(self):
    self.view = sublime.active_window().active_view()

  def run(self, bracket, content, selection):
    return (bracket.a, bracket.b, content.a, content.b, selection)
