#!/usr/bin/env python
"""
Cross-platform alternative to the Makefile.
Run with: python run.py [command]
Example: python run.py all
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd, shell=False):
    """Run a command and display its output in real-time."""
    print(f"Running: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")

    if shell and not isinstance(cmd, str):
        cmd = " ".join(cmd)

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=shell,
            universal_newlines=True,
        )

        for line in process.stdout:
            print(line, end="")

        process.wait()

        if process.returncode != 0:
            print(f"Command failed with exit code {process.returncode}")
            return False

        return True
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def clean():
    """Remove build artifacts and cache files."""
    print("Cleaning project...")
    paths_to_remove = [
        "build",
        "dist",
        ".pytest_cache",
        ".coverage",
        "coverage.xml",
    ]

    # Add egg-info directories
    paths_to_remove.extend(list(Path(".").glob("*.egg-info")))

    for path in paths_to_remove:
        path = Path(path)
        if path.exists():
            print(f"Removing {path}")
            if path.is_file():
                try:
                    path.unlink()
                except PermissionError:
                    print(f"  Warning: Could not remove file {path} (permission denied)")
            else:
                try:
                    shutil.rmtree(path)
                except (PermissionError, OSError) as e:
                    print(f"  Warning: Could not remove directory {path} ({e})")

    # Remove __pycache__ directories but exclude .venv directory
    for pycache in Path(".").glob("**/__pycache__"):
        # Skip if the path contains .venv
        if ".venv" in str(pycache):
            continue
        print(f"Removing {pycache}")
        try:
            shutil.rmtree(pycache)
        except (PermissionError, OSError) as e:
            print(f"  Warning: Could not remove {pycache} ({e})")

    return True


def format_code():
    """Format code with black and isort."""
    print("Formatting code...")
    black_result = run_command(["black", "logeverything", "tests"])
    isort_result = run_command(["isort", "--profile", "black", "logeverything", "tests"])
    return black_result and isort_result


def lint():
    """Run linting tools."""
    print("Running linters...")
    commands = [
        ["flake8", "logeverything"],
        ["black", "--check", "logeverything", "tests"],
        ["isort", "--check-only", "--profile", "black", "logeverything", "tests"],
        ["mypy", "logeverything"],
        ["bandit", "-r", "logeverything"],
    ]

    success = True
    for cmd in commands:
        if not run_command(cmd):
            success = False

    return success


def test(verbose=False):
    """Run tests with pytest."""
    print("Running tests...")
    cmd = ["pytest", "--cov=logeverything", "tests/"]
    if verbose:
        cmd.insert(1, "-v")

    return run_command(cmd)


def build_docs():
    """Build documentation with Sphinx."""
    print("Building documentation...")
    os.chdir("docs")
    result = run_command(["sphinx-build", "-b", "html", "source", "build/html"])
    os.chdir("..")
    return result


def view_docs():
    """Open documentation in browser."""
    print("Opening documentation...")
    docs_path = Path("docs/build/html/index.html").absolute().as_uri()

    if platform.system() == "Windows":
        run_command(["powershell", "-c", f"Start-Process '{docs_path}'"], shell=True)
    elif platform.system() == "Darwin":  # macOS
        run_command(["open", docs_path])
    else:  # Linux and others
        run_command(["xdg-open", docs_path])


def build():
    """Build the package."""
    print("Building package...")
    return run_command([sys.executable, "-m", "build"])


def release():
    """Prepare for release."""
    print("Preparing for release...")
    success = clean() and lint() and test() and build()

    if success:
        print("\nReady to release! Run: twine upload dist/*")

    return success


def all_commands():
    """Run all commands in sequence."""
    steps = [
        ("Cleaning", clean),
        ("Formatting", format_code),
        ("Linting", lint),
        ("Testing", test),
        ("Building docs", build_docs),
        ("Building package", build),
    ]

    success = True
    for step_name, step_fn in steps:
        print(f"\n=== {step_name} ===\n")
        if not step_fn():
            print(f"\n❌ {step_name} failed!\n")
            success = False
            break
        print(f"\n✅ {step_name} completed successfully!\n")

    if success:
        print("\n✨ All commands completed successfully! ✨\n")
    else:
        print("\n❌ Some commands failed! See above for details.\n")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Run development tasks")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # All commands
    subparsers.add_parser("all", help="Run all commands")

    # Individual commands
    subparsers.add_parser("clean", help="Clean build artifacts")
    subparsers.add_parser("format", help="Format code")
    subparsers.add_parser("lint", help="Run linters")
    subparsers.add_parser("test", help="Run tests")
    subparsers.add_parser("test-verbose", help="Run tests with verbose output")
    subparsers.add_parser("docs", help="Build documentation")
    subparsers.add_parser("view-docs", help="View documentation in browser")
    subparsers.add_parser("build", help="Build package")
    subparsers.add_parser("release", help="Prepare for release")

    args = parser.parse_args()

    # Default to "all" if no command is specified
    command = args.command or "all"

    command_funcs = {
        "all": all_commands,
        "clean": clean,
        "format": format_code,
        "lint": lint,
        "test": test,
        "test-verbose": lambda: test(verbose=True),
        "docs": build_docs,
        "view-docs": view_docs,
        "build": build,
        "release": release,
    }

    if command in command_funcs:
        success = command_funcs[command]()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
