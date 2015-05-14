"""Test JSON."""
import unittest
from . import validate_json_format
import os
import fnmatch


class TestSettings(unittest.TestCase):

    """Test JSON settings."""

    def _get_json_files(self, pattern):
        """Get json files."""

        for root, dirnames, filenames in os.walk('.'):
            for filename in fnmatch.filter(filenames, pattern):
                yield os.path.join(root, filename)

    def test_json_settings(self):
        """Test each JSON file."""

        patterns = (
            '*.sublime-settings',
            '*.sublime-keymap',
            '*.sublime-commands',
            '*.sublime-menu',
            '*.sublime-theme'
        )

        for pattern in patterns:
            for f in self._get_json_files(pattern):
                print(f)
                self.assertFalse(
                    validate_json_format.CheckJsonFormat(False, True).check_format(f),
                    "%s does not comform to expected format!" % f
                )
