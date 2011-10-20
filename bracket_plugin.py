import sublime


class BracketPlugin():
    def __init__(self, plugin):
        self.enabled = False
        self.args = plugin['args'] if ("args" in plugin) else {}
        self.plugin = None
        if 'command' in plugin:
            try:
                (module_name, class_name) = plugin['command'].split('.')
                module = __import__(module_name)
                self.plugin = getattr(module, class_name)
                self.enabled = True
            except Exception:
                sublime.error_message('Can not load plugin: ' + plugin['command'])

    def is_enabled(self):
        return self.enabled

    def run_command(self, bracket, content, selection):
        self.args['bracket'] = bracket
        self.args['content'] = content
        self.args['selection'] = selection
        plugin = self.plugin(bracket, content, selection)
        plugin.run(**self.args)
        return plugin.attr.get_attr()


class BracketAttributes():
    def __init__(self, bracket, content, selection):
        self.bracket = bracket
        self.content = content
        self.selection = selection

    def set_bracket(self, bracket):
        self.bracket = bracket

    def set_content(self, content):
        self.content = content

    def set_selection(self, selection):
        self.selection = selection

    def get_attr(self):
        return (self.bracket, self.content, self.selection)


class BracketPluginCommand():
    def __init__(self, bracket, content, selection):
        self.view = sublime.active_window().active_view()
        self.attr = BracketAttributes(bracket, content, selection)

    def run(self, bracket, content, selection):
        pass
