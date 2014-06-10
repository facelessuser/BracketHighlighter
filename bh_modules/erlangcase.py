def validate(name, bracket, bracket_side, bfr):
    """
    Check if bracket is lowercase
    """

    return bfr[bracket.begin:bracket.end].islower()
