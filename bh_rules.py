import BracketHighlighter.ure as ure
import BracketHighlighter.bh_plugin as bh_plugin
from BracketHighlighter.bh_logging import debug, log
from operator import itemgetter
import sublime
import sublime_plugin

BH_STYLE = "default"
BH_ENABLED = True
BH_LANG_LIST = []
BH_LANG_FILTER = "blacklist"
BH_FIND_SUB = "false"
BH_SUB_BRACKET = "false"
BH_COMPARE_MATCH = None
BH_POST_MATCH = None
BH_VALIDATE_MATCH = None
BH_SCOPE_EXCLUDE = []
BH_SCOPE_EXCLUDE_EXCEPTIONS = []
BH_IGNORE_STRING_ESCAPE = False
BH_PLUGIN_LIB = None


def exclude_bracket(enabled, filter_type, language_list, language):
    """
    Exclude or include brackets based on filter lists.
    """

    exclude = True
    if enabled:
        # Black list languages
        if filter_type == 'blacklist':
            exclude = False
            if language is not None:
                for item in language_list:
                    if language == item.lower():
                        exclude = True
                        break
        # White list languages
        elif filter_type == 'whitelist':
            if language is not None:
                for item in language_list:
                    if language == item.lower():
                        exclude = False
                        break
    return exclude


def process_overrides(rules):
    """
    Walk the list and merge override rules
    """

    final = []
    names = {}
    replace = {}
    pos = 0
    indexes = set()
    for rule in rules:
        name = rule.get("name")
        if name is None:
            continue
        if name in names:
            if name in replace:
                # Merge current override with previous overrides
                replace[name] = dict(list(replace[name].items()) + list(rule.items()))
            else:
                # Add override
                replace[name] = rule
        else:
            # Add name and track position
            names[name] = pos
            final.append(rule)
        pos += 1
    if len(replace):
        # Walk the final replace dict,
        # and override the rule in the final array
        for k, v in replace.items():
            pos = names[k]
            final[pos] = dict(list(final[pos].items()) + list(v.items()))

    # Track which positions are specified
    # If an postition index has aleady been
    # specified or is invalid, discard the index.
    for rule in final:
        index = rule.get("position")
        if index is not None:
            if isinstance(index, int) and index > 0 and index not in indexes:
                indexes.add(rule["position"])
            else:
                del rule["position"]

    # Ensure all rules have a position index
    pos = 0
    for rule in final:
        index = rule.get("position", None)
        if index is None:
            while pos in indexes:
                pos += 1
            rule["position"] = pos
            indexes.add(pos)
            pos += 1

    # Sort by position and return
    return sorted(final, key=itemgetter('position'))


def is_valid_definition(params, language):
    """
    Ensure bracket definition should be and can be loaded.
    """

    return (
        not exclude_bracket(
            params.get("enabled", BH_ENABLED),
            params.get("language_filter", BH_LANG_FILTER),
            params.get("language_list", BH_LANG_LIST),
            language
        ) and
        params["open"] is not None and params["close"] is not None
    )


class BracketDefinition(object):
    """
    Normal bracket definition.
    """

    def __init__(self, bracket):
        """
        Setup the bracket object by reading the passed in dictionary.
        """

        self.name = bracket["name"]
        self.style = bracket.get("style", BH_STYLE)
        self.compare = bracket.get("compare", BH_COMPARE_MATCH)
        sub_search = bracket.get("find_in_sub_search", BH_FIND_SUB)
        self.find_in_sub_search_only = sub_search == "only"
        self.find_in_sub_search = sub_search == "true" or self.find_in_sub_search_only
        self.post_match = bracket.get("post_match", BH_POST_MATCH)
        self.validate = bracket.get("validate", BH_VALIDATE_MATCH)
        self.scope_exclude_exceptions = bracket.get("scope_exclude_exceptions", BH_SCOPE_EXCLUDE_EXCEPTIONS)
        self.scope_exclude = bracket.get("scope_exclude", BH_SCOPE_EXCLUDE)
        self.ignore_string_escape = bracket.get("ignore_string_escape", BH_IGNORE_STRING_ESCAPE)


class ScopeDefinition(object):
    """
    Scope bracket definition.
    """

    def __init__(self, bracket):
        """
        Setup the bracket object by reading the passed in dictionary.
        """

        self.style = bracket.get("style", BH_STYLE)
        self.open = ure.compile("\\A" + bracket.get("open", "."), ure.MULTILINE | ure.IGNORECASE)
        self.close = ure.compile(bracket.get("close", ".") + "\\Z", ure.MULTILINE | ure.IGNORECASE)
        self.name = bracket["name"]
        sub_search = bracket.get("sub_bracket_search", BH_SUB_BRACKET)
        self.sub_search_only = sub_search == "only"
        self.sub_search = self.sub_search_only is True or sub_search == "true"
        self.compare = bracket.get("compare", BH_COMPARE_MATCH)
        self.post_match = bracket.get("post_match", BH_POST_MATCH)
        self.validate = bracket.get("validate", BH_VALIDATE_MATCH)
        self.scopes = bracket["scopes"]


class SearchRules(object):
    def __init__(self, brackets, scopes, string_escape_mode, outside_adj):
        self.bracket_rules = process_overrides(brackets)
        self.scope_rules = process_overrides(scopes)
        self.enabled = False
        self.string_escape_mode = string_escape_mode
        self.outside_adj = outside_adj

    def load_rules(self, language, modules):
        self.enabled = False
        self.brackets = []
        self.scopes = []
        self.check_compare = False
        self.check_validate = False
        self.check_post_match = False
        self.parse_bracket_definition(language, modules)
        self.parse_scope_definition(language, modules)
        if len(self.scopes) or len(self.brackets):
            self.enabled = True

    def parse_bracket_definition(self, language, loaded_modules):
        """
        Parse the bracket defintion
        """

        names = []
        subnames = []
        find_regex = []
        sub_find_regex = []

        for params in self.bracket_rules:
            if is_valid_definition(params, language):
                try:
                    bh_plugin.load_modules(params, loaded_modules)
                    entry = BracketDefinition(params)
                    if not self.check_compare and entry.compare is not None:
                        self.check_compare = True
                    if not self.check_validate and entry.validate is not None:
                        self.check_validate = True
                    if not self.check_post_match and entry.post_match is not None:
                        self.check_post_match = True
                    self.brackets.append(entry)
                    if not entry.find_in_sub_search_only:
                        find_regex.append(params["open"])
                        find_regex.append(params["close"])
                        names.append(params["name"])
                    else:
                        find_regex.append(r"([^\s\S])")
                        find_regex.append(r"([^\s\S])")

                    if entry.find_in_sub_search:
                        sub_find_regex.append(params["open"])
                        sub_find_regex.append(params["close"])
                        subnames.append(params["name"])
                    else:
                        sub_find_regex.append(r"([^\s\S])")
                        sub_find_regex.append(r"([^\s\S])")
                except Exception as e:
                    log(e)

        if len(self.brackets):
            self.brackets = tuple(self.brackets)
            debug(
                "Bracket Pattern: (%s)\n" % ','.join(names) +
                "    (Opening|Closing):     (?:%s)\n" % '|'.join(find_regex)
            )
            debug(
                "SubBracket Pattern: (%s)\n" % ','.join(subnames) +
                "    (Opening|Closing): (?:%s)\n" % '|'.join(sub_find_regex)
            )
            self.sub_pattern = ure.compile("(?:%s)" % '|'.join(sub_find_regex), ure.MULTILINE | ure.IGNORECASE)
            self.pattern = ure.compile("(?:%s)" % '|'.join(find_regex), ure.MULTILINE | ure.IGNORECASE)

    def parse_scope_definition(self, language, loaded_modules):
        """
        Parse the scope defintion
        """

        scopes = {}
        scope_count = 0
        for params in self.scope_rules:
            if is_valid_definition(params, language):
                try:
                    bh_plugin.load_modules(params, loaded_modules)
                    entry = ScopeDefinition(params)
                    if not self.check_compare and entry.compare is not None:
                        self.check_compare = True
                    if not self.check_validate and entry.validate is not None:
                        self.check_validate = True
                    if not self.check_post_match and entry.post_match is not None:
                        self.check_post_match = True
                    for x in entry.scopes:
                        if x not in scopes:
                            scopes[x] = scope_count
                            scope_count += 1
                            self.scopes.append({"name": x, "brackets": [entry]})
                        else:
                            self.scopes[scopes[x]]["brackets"].append(entry)
                    debug("Scope Regex (%s)\n    Opening: %s\n    Closing: %s\n" % (entry.name, entry.open.pattern, entry.close.pattern))
                except Exception as e:
                    log(e)


####################
# Debug
####################
class BhDebugRuleEditCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        self.view.insert(edit, self.view.size(), text)


class BhDebugRuleCommand(sublime_plugin.WindowCommand):
    filter_keys = [
        "name",
        "open",
        "close",
        "style",
        "enabled",
        "position",
        "language_filter",
        "language_list",
        "plugin_library",
        "find_in_sub_search",
        "scope_exclude",
        "scope_exclude_exceptions",
        "ignore_string_escape",
        "scopes",
        "sub_bracket_search"
    ]

    def run(self, filter_key=False):
        if not filter_key:
            self.show()
        else:
            self.window.show_quick_panel(self.filter_keys, self.show)

    def show(self, key=None):
        self.text = []
        if key is not None and key > -1:
            self.key = self.filter_keys[key]
            label = "Rule \"%s\"" % self.key
            self.fn = self.show_key
        elif key is None:
            self.key = None
            label = "Merged Rules"
            self.fn = self.show_merged
        else:
            return
        settings = sublime.load_settings("bh_core.sublime-settings")
        brackets = settings.get("brackets", []) + settings.get("user_brackets", [])
        scopes = settings.get("scope_brackets", []) + settings.get("user_scope_brackets", [])
        view = self.window.new_file()
        view.run_command(
            "bh_debug_rule_edit",
            {
                "text": self.show_rules(brackets, scopes)
            }
        )
        view.set_name("[bh_debug] %s" % label)
        view.set_read_only(True)
        view.set_scratch(True)

    def show_merged(self, rule):
        import json
        self.text.append("        {\n")
        rule_count = 0
        rule_length = len(rule) - 1
        for k, v in rule.items():
            self.text.append('            "%s": %s' % (k, json.dumps(v)))
            self.text.append("\n" if rule_count == rule_length else ",\n")
            rule_count += 1
        self.text.append("        }")

    def show_key(self, rule):
        import json
        if self.key in rule:
            self.text.append(
                '        {"name": "%s", "%s": %s}' % (
                    rule["name"], self.key, json.dumps(rule.get(self.key))
                )
            )

    def show_rules(self, brackets, scopes):
        from collections import OrderedDict
        self.text = ["[\n"]
        rules_count = 0
        for rules in [process_overrides(brackets), process_overrides(scopes)]:
            self.text.append("    [\n")
            length = len(rules) - 1
            rule_count = 0
            for rule in rules:
                if rules_count == 0:
                    item = OrderedDict(
                        (
                            ("name", rule.get("name")),
                            ("open", rule.get("open")),
                            ("close", rule.get("close")),
                            ("style", rule.get("style", BH_STYLE)),
                            ("enabled", rule.get("enabled", BH_ENABLED)),
                            ("position", rule.get("position")),
                            ("language_filter", rule.get("language_filter", BH_LANG_FILTER)),
                            ("language_list", rule.get("language_list", BH_LANG_LIST)),
                            ("plugin_library", rule.get("plugin_library", BH_PLUGIN_LIB)),
                            ("find_in_sub_search", rule.get("find_in_sub_search", BH_FIND_SUB)),
                            ("scope_exclude", rule.get("scope_exclude", BH_SCOPE_EXCLUDE)),
                            ("scope_exclude_exceptions", rule.get("scope_exclude_exceptions", BH_SCOPE_EXCLUDE_EXCEPTIONS)),
                            ("ignore_string_escape", rule.get("ignore_string_escape", BH_IGNORE_STRING_ESCAPE))
                        )
                    )
                else:
                    item = OrderedDict(
                        (
                            ("name", rule.get("name")),
                            ("open", rule.get("open")),
                            ("close", rule.get("close")),
                            ("style", rule.get("style", BH_STYLE)),
                            ("scopes", rule.get("scopes")),
                            ("enabled", rule.get("enabled", BH_ENABLED)),
                            ("position", rule.get("position")),
                            ("language_filter", rule.get("language_filter", BH_LANG_FILTER)),
                            ("language_list", rule.get("language_list", BH_LANG_LIST)),
                            ("plugin_library", rule.get("plugin_library", BH_PLUGIN_LIB)),
                            ("sub_bracket_search", rule.get("sub_bracket_search", BH_SUB_BRACKET))
                        )
                    )
                self.fn(item)
                self.text.append("\n" if rule_count == length else ",\n")
                rule_count += 1
            self.text.append("    ]\n" if rules_count == 1 else "    ],\n")
            rules_count += 1
        self.text.append("]\n")
        return ''.join(self.text)

    def is_enabled(self):
        return sublime.load_settings("bh_core.sublime-settings").get('debug_enable', False)
