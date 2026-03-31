"""
Test script for checking that we've fixed the environment detection bug.
This script will mock different environment combinations and verify that
the environment detection works as expected.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logeverything.core import _detect_environment


class TestEnvironmentDetection(unittest.TestCase):
    """Test that environment detection properly prioritizes notebooks over web frameworks."""

    def test_notebook_takes_priority(self):
        """Test that notebook detection takes priority over web app detection."""
        # Mock both ipykernel and flask being present
        with patch.dict("sys.modules", {"ipykernel": MagicMock(), "flask": MagicMock()}):
            # Should detect notebook, not web_app
            self.assertEqual(_detect_environment(), "notebook")

    def test_web_app_detection(self):
        """Test that web app is detected correctly when there's no notebook."""
        # Mock flask being present
        with patch.dict("sys.modules", {"flask": MagicMock()}):
            # No sys.argv would make this an unknown or web_app
            with patch("sys.argv", []):
                self.assertEqual(_detect_environment(), "web_app")

    def test_script_detection(self):
        """Test that script is detected correctly."""
        # Not in notebook or web app
        with patch.dict("sys.modules", {}):
            # Script has a .py extension
            with patch("sys.argv", ["script.py"]):
                with patch("os.path.basename", return_value="script.py"):
                    self.assertEqual(_detect_environment(), "script")


if __name__ == "__main__":
    unittest.main()
