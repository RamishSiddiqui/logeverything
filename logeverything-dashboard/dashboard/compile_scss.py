"""
SCSS compilation script for LogEverything Dashboard
"""

import glob
import os
import time
from pathlib import Path

import sass
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class SCSSCompiler:
    """Compiler for SCSS files to CSS."""

    def __init__(self, scss_dir, css_dir):
        self.scss_dir = Path(scss_dir)
        self.css_dir = Path(css_dir)
        self.css_dir.mkdir(exist_ok=True)

    def compile_all(self):
        """Compile all SCSS files in the directory."""
        main_file = self.scss_dir / "main.scss"
        output_file = self.css_dir / "styles.css"

        if not main_file.exists():
            print(f"Error: Main SCSS file not found at {main_file}")
            return

        try:
            print(f"Compiling {main_file} to {output_file}")
            css = sass.compile(
                filename=str(main_file),
                output_style="compressed",
                include_paths=[str(self.scss_dir)],
            )

            with open(output_file, "w") as f:
                f.write(css)

            print(f"Successfully compiled SCSS to {output_file}")
        except Exception as e:
            print(f"Error compiling SCSS: {e}")

    def watch(self):
        """Watch for changes in SCSS files and recompile."""
        event_handler = SCSSChangeHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.scss_dir), recursive=True)
        observer.start()

        try:
            print(f"Watching for changes in {self.scss_dir}")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()


class SCSSChangeHandler(FileSystemEventHandler):
    """Handler for SCSS file changes."""

    def __init__(self, compiler):
        self.compiler = compiler

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and event.src_path.endswith(".scss"):
            print(f"Change detected in {event.src_path}")
            self.compiler.compile_all()


def main():
    """Main entry point for SCSS compilation."""
    # Get the absolute path to the dashboard directory
    base_dir = Path(__file__).parent
    scss_dir = base_dir / "static" / "scss"
    css_dir = base_dir / "static" / "css"

    compiler = SCSSCompiler(scss_dir, css_dir)
    compiler.compile_all()

    # Watch for changes if requested
    if "--watch" in os.sys.argv:
        compiler.watch()


if __name__ == "__main__":
    main()
