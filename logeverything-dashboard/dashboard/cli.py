"""
CLI entry point for LogEverything Dashboard.

Usage:
    logeverything-dashboard                  # start on default port 3001
    logeverything-dashboard --port 8080      # custom port
    logeverything-dashboard --data-dir ./logs # point to a log directory
"""

import argparse
import os
import threading
from pathlib import Path


def compile_scss():
    """Compile SCSS files to CSS."""
    try:
        from dashboard.compile_scss import SCSSCompiler

        base_dir = Path(__file__).parent
        scss_dir = base_dir / "static" / "scss"
        css_dir = base_dir / "static" / "css"

        css_dir.mkdir(parents=True, exist_ok=True)

        compiler = SCSSCompiler(scss_dir, css_dir)
        compiler.compile_all()
        print("SCSS compilation complete")
        return True
    except Exception as e:
        print(f"Warning: SCSS compilation failed: {e}")
        print("Using existing CSS files if available")
        return False


def run_scss_watcher():
    """Run SCSS watcher in a background thread."""
    from dashboard.compile_scss import SCSSCompiler

    base_dir = Path(__file__).parent
    scss_dir = base_dir / "static" / "scss"
    css_dir = base_dir / "static" / "css"

    compiler = SCSSCompiler(scss_dir, css_dir)
    compiler.watch()


def main():
    """Main entry point for the logeverything-dashboard command."""
    parser = argparse.ArgumentParser(description="Run LogEverything Dashboard")
    parser.add_argument("--port", type=int, default=3001, help="Port to run on (default: 3001)")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--no-scss-watch", action="store_true", help="Disable SCSS file watcher")
    parser.add_argument("--data-dir", type=str, help="Data directory containing log files")
    parser.add_argument("--api-url", type=str, help="Remote LogEverything API URL")
    parser.add_argument("--version", action="store_true", help="Show version and exit")

    args = parser.parse_args()

    if args.version:
        from dashboard import __version__

        print(f"logeverything-dashboard {__version__}")
        return

    # Set environment variables from CLI args
    if args.data_dir:
        os.environ["DASHBOARD_MONITORING_DATA_DIR"] = args.data_dir
    if args.api_url:
        os.environ["DASHBOARD_API_URL"] = args.api_url

    os.environ["DASHBOARD_DASHBOARD_PORT"] = str(args.port)

    # Compile SCSS
    compile_scss()

    # Start SCSS watcher in background
    if not args.no_scss_watch:
        watcher_thread = threading.Thread(target=run_scss_watcher, daemon=True)
        watcher_thread.start()

    # Start the server
    import uvicorn

    print(f"Starting LogEverything Dashboard at http://localhost:{args.port}")
    uvicorn.run(
        "dashboard.main:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
