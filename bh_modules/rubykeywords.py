import re


def post_match(view, name, style, first, second, center, bfr, threshold):
    if first is not None:
        # Strip whitespace from the beginning of first bracket
        open_bracket = bfr[first.begin:first.end]
        print (open_bracket)
        if open_bracket != "do":
            m = re.match(r"(\s*\b)[\w\W]*", open_bracket)
            if m:
                first = first.move(first.begin + m.end(1), first.end)
    return first, second, style
