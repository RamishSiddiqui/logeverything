"""
LogEverything CLI -- diagnostic and scaffolding utilities.

Usage::

    logeverything version    Print version, Python version, platform
    logeverything doctor     Check environment and optional dependencies
    logeverything init       Generate a starter logging_config.py
"""

import argparse
import importlib
import os
import platform
import socket
import sys

# Unicode check/cross marks with ASCII fallback for legacy Windows consoles
_CHECK = "\u2713"
_CROSS = "\u2717"


def _safe_print(text: str) -> None:
    """Print text with a fallback for terminals that cannot encode Unicode."""
    try:
        print(text)
    except UnicodeEncodeError:
        ascii_text = text.replace(_CHECK, "+").replace(_CROSS, "X")
        print(ascii_text)


def cmd_version() -> None:
    """Print version, Python version, and platform."""
    from logeverything import __version__

    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"logeverything {__version__}")
    print(f"Python {py_version}")
    print(f"Platform: {platform.platform()}")


def cmd_doctor() -> None:
    """Check environment: Python, platform, optional packages, py.typed, dashboard."""
    from logeverything import __version__

    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    _safe_print("logeverything doctor")

    # Python version
    _safe_print(f"  [{_CHECK}] Python {py_version}")

    # Platform
    _safe_print(f"  [{_CHECK}] Platform: {platform.platform()}")

    # Optional packages
    optional_packages = [
        "fastapi",
        "celery",
        "orjson",
        "rich",
        "psutil",
        "aiohttp",
    ]
    for pkg_name in optional_packages:
        try:
            mod = importlib.import_module(pkg_name)
            version = getattr(mod, "__version__", "installed")
            _safe_print(f"  [{_CHECK}] {pkg_name} {version}")
        except ImportError:
            _safe_print(f"  [{_CROSS}] {pkg_name} (not installed)")

    # py.typed marker
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    py_typed = os.path.join(pkg_dir, "py.typed")
    if os.path.exists(py_typed):
        _safe_print(f"  [{_CHECK}] py.typed marker present")
    else:
        _safe_print(f"  [{_CROSS}] py.typed marker missing")

    # Dashboard connectivity
    try:
        sock = socket.create_connection(("localhost", 8999), timeout=2)
        sock.close()
        _safe_print(f"  [{_CHECK}] Dashboard at localhost:8999 (reachable)")
    except (OSError, socket.timeout):
        _safe_print(f"  [{_CROSS}] Dashboard at localhost:8999 (not reachable)")

    # Registered loggers
    try:
        from logeverything.core import _active_loggers

        count = len(_active_loggers)
        _safe_print(f"  [{_CHECK}] {count} registered loggers")
    except Exception:
        _safe_print(f"  [{_CROSS}] Unable to check registered loggers")


_TEMPLATES = {
    "web": """\
from logeverything import Logger, log

logger = Logger("app", log_file="app.log", level="INFO")

@log
def handle_request(request):
    logger.info("Processing request")
""",
    "script": """\
from logeverything import Logger, log

logger = Logger("script", level="DEBUG")

@log
def main():
    logger.info("Script started")

if __name__ == "__main__":
    main()
""",
    "notebook": """\
from logeverything import Logger

logger = Logger("notebook", level="DEBUG")
logger.info("Notebook initialized")
""",
}


def cmd_init() -> None:
    """Interactive wizard to generate a starter logging_config.py."""
    print("LogEverything project initializer")
    print()
    print("Select environment type:")
    print("  1) web      -- Web application (FastAPI / Flask / Django)")
    print("  2) script   -- Standalone script or CLI tool")
    print("  3) notebook -- Jupyter notebook")
    print()

    choice = input("Enter choice [1/2/3] (default: 2): ").strip() or "2"
    env_map = {
        "1": "web",
        "2": "script",
        "3": "notebook",
        "web": "web",
        "script": "script",
        "notebook": "notebook",
    }
    env_type = env_map.get(choice, "script")

    output_path = "logging_config.py"
    if os.path.exists(output_path):
        overwrite = input(f"{output_path} already exists. Overwrite? [y/N]: ").strip().lower()
        if overwrite != "y":
            print("Aborted.")
            return

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(_TEMPLATES[env_type])

    print(f"Created {output_path} ({env_type} template)")


def main() -> None:
    """Entry point for the logeverything CLI."""
    parser = argparse.ArgumentParser(
        prog="logeverything",
        description="LogEverything CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("version", help="Show version info")
    subparsers.add_parser("doctor", help="Check environment")
    subparsers.add_parser("init", help="Generate starter config")

    args = parser.parse_args()

    if args.command == "version":
        cmd_version()
    elif args.command == "doctor":
        cmd_doctor()
    elif args.command == "init":
        cmd_init()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
