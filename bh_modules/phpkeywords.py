def compare(name, first, second, bfr):
    """
    Pair the appropriate open bracket with its close
    """

    return "end" + bfr[first.begin:first.end].lower() == bfr[second.begin:second.end].lower()
