"""Test JSON."""
import unittest
from . import validate_json_format


class TestSettings(unittest.TestCase):

    """Test JSON settings."""

    def test_json_settings(self):
        """Test each JSON file."""

        files = [
            "bh_swapping.sublime-settings",
            "bh_wrapping.sublime-settings",
            "Default.sublime-keymap",
            "Default.sublime-commands",
            "bh_core.sublime-settings"
        ]

        for f in files:
            self.assertFalse(
                validate_json_format.CheckJsonFormat(False, True).check_format(f),
                "%s does not comform to expected format!" % f
            )
