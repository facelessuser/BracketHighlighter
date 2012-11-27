def compare(name, first, second, bfr):
    return "end" + bfr[first.begin:first.end].lower() == bfr[second.begin:second.end].lower()
