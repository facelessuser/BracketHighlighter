import ure
import bh_plugin
from bh_logging import debug, log


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


def is_valid_definition(params, language):
    """
    Ensure bracket definition should be and can be loaded.
    """

    return (
        not exclude_bracket(
            params.get("enabled", True),
            params.get("language_filter", "blacklist"),
            params.get("language_list", []),
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
        self.style = bracket.get("style", "default")
        self.compare = bracket.get("compare")
        sub_search = bracket.get("find_in_sub_search", "false")
        self.find_in_sub_search_only = sub_search == "only"
        self.find_in_sub_search = sub_search == "true" or self.find_in_sub_search_only
        self.post_match = bracket.get("post_match")
        self.validate = bracket.get("validate")
        self.scope_exclude_exceptions = bracket.get("scope_exclude_exceptions", [])
        self.scope_exclude = bracket.get("scope_exclude", [])
        self.ignore_string_escape = bracket.get("ignore_string_escape", False)


class ScopeDefinition(object):
    """
    Scope bracket definition.
    """

    def __init__(self, bracket):
        """
        Setup the bracket object by reading the passed in dictionary.
        """

        self.style = bracket.get("style", "default")
        self.open = ure.compile("\\A" + bracket.get("open", "."), ure.MULTILINE | ure.IGNORECASE)
        self.close = ure.compile(bracket.get("close", ".") + "\\Z", ure.MULTILINE | ure.IGNORECASE)
        self.name = bracket["name"]
        sub_search = bracket.get("sub_bracket_search", "false")
        self.sub_search_only = sub_search == "only"
        self.sub_search = self.sub_search_only is True or sub_search == "true"
        self.compare = bracket.get("compare")
        self.post_match = bracket.get("post_match")
        self.validate = bracket.get("validate")
        self.scopes = bracket["scopes"]


class SearchRules(object):
    def __init__(self, brackets, scopes, string_escape_mode, outside_adj):
        self.bracket_rules = brackets
        self.scope_rules = scopes
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
