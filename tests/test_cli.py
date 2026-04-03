"""Tests for the logeverything CLI tool."""

import subprocess
import sys

PYTHON = sys.executable


class TestCLIVersion:
    def test_version_output(self):
        result = subprocess.run(
            [PYTHON, "-m", "logeverything.cli", "version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "logeverything" in result.stdout.lower()

    def test_version_via_module(self):
        result = subprocess.run(
            [PYTHON, "-m", "logeverything", "version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "logeverything" in result.stdout.lower()


class TestCLIDoctor:
    def test_doctor_runs(self):
        result = subprocess.run(
            [PYTHON, "-m", "logeverything.cli", "doctor"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Python" in result.stdout


class TestCLINoArgs:
    def test_no_args_shows_help(self):
        result = subprocess.run(
            [PYTHON, "-m", "logeverything.cli"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
