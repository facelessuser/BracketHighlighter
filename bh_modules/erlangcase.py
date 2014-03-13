def validate(name, bracket, bracket_side, bfr):
    text = bfr[bracket.begin:bracket.end]
    return text.lower() == text
