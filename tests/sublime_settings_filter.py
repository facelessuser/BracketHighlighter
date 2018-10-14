"""Sublime settings parser."""
import re
import codecs
from pyspelling import filters
import textwrap

RE_LINE_PRESERVE = re.compile(r"\r?\n", re.MULTILINE)
RE_COMMENT = re.compile(
    r'''(?x)
        (?P<comments>
            (?P<block>/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)                        # multi-line comments
          | (?P<start>^)?(?P<leading_space>[ \t]*)?(?P<line>//(?:[^\r\n])*)  # single line comments
        )
      | (?P<code>
            "(?:\\.|[^"\\])*"                                  # double quotes
          | .[^/"']*?                                           # everything else
        )
    ''',
    re.DOTALL | re.MULTILINE
)


class SublimeSettingsFilter(filters.Filter):
    """Spelling Sublime settings."""

    def __init__(self, options, default_encoding='ascii'):
        """Initialization."""

        self.blocks = options.get('block_comments', True) is True
        self.lines = options.get('line_comments', True) is True
        # self.strings = options.get('strings', False) is True
        self.group_comments = options.get('group_comments', False) is True

        super(SublimeSettingsFilter, self).__init__(options, default_encoding)

    def _evaluate(self, m):
        """Search for comments."""

        g = m.groupdict()
        if g["code"]:
            text = g["code"]
            self.lines += text.count('\n')
        else:
            if g['block'] and self.blocks:
                self.block_comments.append([g['block'][2:-2], self.lines])
                self.lines += g['comments'].count('\n')
            elif self.lines:
                if g['start'] is None:
                    self.line_comments.append([g['line'][2:], self.lines])
                    self.lines += g['comments'].count('\n')
                else:
                    # Cosecutive lines with only comments with same leading whitespace
                    # will be captured as a single block.
                    if self.group_comments and self.lines == self.prev_line + 1 and g['leading_space'] == self.leading:
                        self.line_comments[-1][0] += '\n' + g['line'][2:]
                    else:
                        self.line_comments.append([g['line'][2:], self.lines])
                    self.leading = g['leading_space']
                    self.lines += g['comments'].count('\n')
                    self.prev_line = self.lines
            else:
                self.lines += g['comments'].count('\n')
            text = ''.join([x[0] for x in RE_LINE_PRESERVE.findall(g["comments"])])
        return text

    def _filter(self, text, context, encoding):
        """Perform actual filtering."""

        content = []
        self.lines = 1
        self.prev_line = -1
        self.leading = ''
        self.block_comments = []
        self.line_comments = []

        text = self._find_comments(text)
        for comment, line in self.block_comments:
            content.append(
                filters.SourceText(
                    textwrap.dedent(comment),
                    "%s (%d)" % (context, line),
                    encoding,
                    'block-comment'
                )
            )
        for comment, line in self.line_comments:
            content.append(
                filters.SourceText(
                    textwrap.dedent(comment),
                    "%s (%d)" % (context, line),
                    encoding,
                    'line-comment'
                )
            )

        return content

    def _find_comments(self, text):
        """Find comments."""

        return ''.join(map(lambda m: self._evaluate(m), RE_COMMENT.finditer(text)))

    def filter(self, source_file, encoding):  # noqa A001
        """Parse HTML file."""

        with codecs.open(source_file, 'r', encoding=encoding) as f:
            return self._filter(f.read(), source_file, encoding)

    def sfilter(self, source):
        """String filter."""

        return self._filter(source.text, source.context, source.encoding)


def get_filter():
    """Get filter."""

    return SublimeSettingsFilter
