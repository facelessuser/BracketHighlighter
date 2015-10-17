"""
Compatibility abstraction.

Licensed under MIT
Copyright (c) 2011 - 2015 Isaac Muse <isaacmuse@gmail.com>
"""
import sys

PY3 = (3, 0) <= sys.version_info < (4, 0)

if PY3:
    string_type = str  # noqa
    binary_type = bytes  # noqa

    def iterstring(string):
        """Iterate through a string."""

        if isinstance(string, binary_type):
            for x in range(0, len(string)):
                yield string[x:x + 1]
        else:
            for c in string:
                yield c

    class Tokens(object):
        """Tokens base for PY3."""

        def iternext(self):
            """Common override method."""

        def __next__(self):
            """PY3 iterator compatible next."""

            return self.iternext()

else:
    string_type = basestring  # noqa
    binary_type = str  # noqa

    def iterstring(string):
        """Iterate through a string."""

        for c in string:
            yield c

    class Tokens(object):
        """Tokens base for PY2."""

        def iternext(self):
            """Common override method."""

        def next(self):
            """PY2 iterator compatible next."""

            return self.iternext()
