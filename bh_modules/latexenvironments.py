"""Compare environments to ensure they have matching names."""
import re

BEGIN_RE = re.compile(r"\\begin\{([^\}]*)\}")
END_RE = re.compile(r"\\end\{([^\}]*)\}")

BEGIN_LEN = len("\\begin{")
END_LEN = len("\\end{")
BRACKET_LEN = len("}")


def highlighting(view, name, style, left, right):
    """Highlight only the environment name."""
    if left is not None:
        left = left.move(left.begin + BEGIN_LEN, left.end - BRACKET_LEN)
    if right is not None:
        right = right.move(right.begin + END_LEN, right.end - BRACKET_LEN)

    return left, right


def compare(name, first, second, bfr):
    """Ensure both environments have the same name."""
    first_match = BEGIN_RE.match(bfr[first.begin:first.end])
    second_match = END_RE.match(bfr[second.begin:second.end])
    # although it should never happen, avoid errors from not matched regex
    if not (first_match and second_match):
        return False

    return first_match.group(1) == second_match.group(1)
