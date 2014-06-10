def validate(name, bracket, bracket_side, bfr):
    """
    Check if bracket is lowercase
    """

    return bfr[bracket.begin:bracket.end].islower()


def compare(name, first, second, bfr):
    """
    Ensure correct open is paired with correct close
    """

    o = bfr[first.begin:first.end]
    c = bfr[second.begin:second.end]

    match = False
    if o == "if" and c == "fi":
        match = True
    elif o in ["select", "for", "while", "until"] and c == "done":
        match = True
    elif o == "case" and c == "esac":
        match = True
    return match
