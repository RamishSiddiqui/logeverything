"""
Sphinx extension for executing code blocks and displaying their output.
"""
import asyncio
import io
import os
import subprocess
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict, List

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.directives.code import CodeBlock
from sphinx.util.docutils import SphinxDirective


class ExecutableCodeDirective(SphinxDirective):
    """
    Directive for executable code blocks that show both code and output.

    Usage:
        .. executable-code::
           :language: python
           :show-output: true

           print("Hello, World!")
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    option_spec = {
        "language": directives.unchanged,
        "show-output": directives.flag,
        "async": directives.flag,
        "hide-code": directives.flag,
        "hide-output": directives.flag,
        "setup": directives.unchanged,
        "teardown": directives.unchanged,
    }

    def run(self) -> List[nodes.Node]:
        """Execute the code and return nodes for both code and output."""

        # Get the code content
        code = "\n".join(self.content)
        language = self.options.get("language", "python")

        # Create container for all output
        container = nodes.container()
        container["classes"] = ["executable-code-container"]

        # Add code block (unless hidden)
        if "hide-code" not in self.options:
            code_node = self._create_code_block(code, language)
            container.append(code_node)

        # Execute code and add output (unless hidden or show-output not specified)
        if "hide-output" not in self.options:
            output = self._execute_code(code, language)
            if output.strip():
                output_node = self._create_output_block(output)
                container.append(output_node)

        return [container]

    def _create_code_block(self, code: str, language: str) -> nodes.literal_block:
        """Create a syntax-highlighted code block."""
        code_node = nodes.literal_block(code, code)
        code_node["language"] = language
        code_node["classes"] = ["executable-code"]
        return code_node

    def _create_output_block(self, output: str) -> nodes.container:
        """Create an output block with special styling."""
        # Create container for output
        output_container = nodes.container()
        output_container["classes"] = ["executable-output"]

        # Add output label
        label = nodes.paragraph()
        label_text = nodes.strong()
        label_text.append(nodes.Text("Output:"))
        label.append(label_text)
        output_container.append(label)

        # Add output content
        output_node = nodes.literal_block(output, output)
        output_node["language"] = "text"
        output_node["classes"] = ["output-content"]
        output_container.append(output_node)

        return output_container

    def _execute_code(self, code: str, language: str) -> str:
        """Execute the code and capture output."""
        if language != "python":
            return f"# Execution not supported for language: {language}"

        # Setup code if specified
        setup_code = self.options.get("setup", "")
        if setup_code:
            code = setup_code + "\n" + code

        # Add teardown code if specified
        teardown_code = self.options.get("teardown", "")
        if teardown_code:
            code = code + "\n" + teardown_code

        try:
            if "async" in self.options:
                return self._execute_async_code(code)
            else:
                return self._execute_sync_code(code)
        except Exception as e:
            return f"Error executing code: {str(e)}\n{traceback.format_exc()}"

    def _execute_sync_code(self, code: str) -> str:
        """Execute synchronous Python code in a subprocess to get real output."""
        import os
        import subprocess
        import tempfile

        # Create a temporary Python file with the code
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp:
            # Add the logeverything directory to Python path
            docs_dir = os.path.dirname(os.path.dirname(__file__))  # source directory
            project_root = os.path.dirname(docs_dir)  # logeverything root

            # Write the complete script
            tmp.write(
                f"""
import sys
import os
sys.path.insert(0, r"{project_root}")

# Force all output to be unbuffered and synchronized
import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Import common modules
import asyncio
import time
import datetime
import json
import tempfile
import uuid
import random

# Import LogEverything components
from logeverything import Logger
from logeverything.asyncio import AsyncLogger
from logeverything.decorators import log, log_function, log_class, log_io
from logeverything.asyncio.async_logging import async_log_function, async_log_class
import logeverything

# Ensure print and logging output are synchronized
class SynchronizedOutput:
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()

    def flush(self):
        self.stream.flush()

    def __getattr__(self, name):
        return getattr(self.stream, name)

# Replace stdout to ensure immediate flushing
sys.stdout = SynchronizedOutput(sys.stdout)

# User code
{code}

# Final flush to ensure all output is captured
sys.stdout.flush()
sys.stderr.flush()
"""
            )
            tmp_path = tmp.name

        try:
            # Execute the script and capture output with proper Unicode support
            # Set environment variables to ensure proper UTF-8 handling and emoji support
            env = os.environ.copy()
            env.update(
                {
                    "PYTHONIOENCODING": "utf-8",
                    "PYTHONLEGACYWINDOWSSTDIO": "0",  # Use new UTF-8 mode on Windows
                    "LANG": "en_US.UTF-8",
                    "LC_ALL": "en_US.UTF-8",
                    "PYTHONUNBUFFERED": "1",  # Force unbuffered output
                }
            )

            result = subprocess.run(
                [sys.executable, "-u", "-X", "utf8", tmp_path],  # -u for unbuffered output
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Redirect stderr to stdout to maintain order
                text=True,
                encoding="utf-8",  # Explicitly use UTF-8 encoding
                timeout=30,  # 30 second timeout
                cwd=project_root,
                env=env,
            )

            # Since stderr is redirected to stdout, we only need stdout
            output = result.stdout or ""

            # Handle any Unicode escape sequences that might have been created
            # This fixes emojis being displayed as \uXXXX codes
            try:
                # First try to decode any literal Unicode escape sequences
                # This handles cases where the subprocess converts emojis to escape sequences
                if "\\u" in output:
                    # Replace common Unicode escape patterns with actual Unicode characters
                    import re

                    # Pattern to match Unicode escape sequences like \u2139\ufe0f
                    unicode_pattern = r"\\u([0-9a-fA-F]{4})"

                    def replace_unicode(match):
                        try:
                            return chr(int(match.group(1), 16))
                        except ValueError:
                            return match.group(0)  # Return original if conversion fails

                    output = re.sub(unicode_pattern, replace_unicode, output)
            except (UnicodeDecodeError, UnicodeError):
                # If decoding fails, keep the original output
                pass

            if result.returncode != 0 and not output:
                output = f"Process exited with code {result.returncode}"

            return output

        except subprocess.TimeoutExpired:
            return "Error: Code execution timed out (30 seconds)"
        except Exception as e:
            return f"Error executing code: {str(e)}"
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except:
                pass

    def _execute_async_code(self, code: str) -> str:
        """Execute asynchronous Python code in a subprocess."""
        # For async code, we need to wrap it properly
        if not code.strip().startswith("async def") and "await " in code:
            # Code contains await but isn't a function, wrap it
            indented_code = "\n".join("    " + line for line in code.split("\n"))
            wrapped_code = f"""
async def _async_main():
{indented_code}

import asyncio
asyncio.run(_async_main())
"""
        else:
            wrapped_code = code

        return self._execute_sync_code(wrapped_code)

    def _create_mock_logger(self):
        """Create a mock logger when LogEverything is not available."""

        class MockLogger:
            def __init__(self, name=None):
                self.name = name or "mock"

            def debug(self, msg, *args, **kwargs):
                formatted_msg = msg % args if args else msg
                if kwargs:
                    kwargs_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
                    formatted_msg = f"{formatted_msg} | {kwargs_str}"
                print(f"2025-06-29 10:30:15 | DEBUG | {self.name} | {formatted_msg}")

            def info(self, msg, *args, **kwargs):
                formatted_msg = msg % args if args else msg
                if kwargs:
                    kwargs_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
                    formatted_msg = f"{formatted_msg} | {kwargs_str}"
                print(f"2025-06-29 10:30:15 | INFO  | {self.name} | {formatted_msg}")

            def warning(self, msg, *args, **kwargs):
                formatted_msg = msg % args if args else msg
                if kwargs:
                    kwargs_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
                    formatted_msg = f"{formatted_msg} | {kwargs_str}"
                print(f"2025-06-29 10:30:15 | WARN  | {self.name} | {formatted_msg}")

            def error(self, msg, *args, **kwargs):
                formatted_msg = msg % args if args else msg
                if kwargs:
                    kwargs_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
                    formatted_msg = f"{formatted_msg} | {kwargs_str}"
                print(f"2025-06-29 10:30:15 | ERROR | {self.name} | {formatted_msg}")

            def critical(self, msg, *args, **kwargs):
                formatted_msg = msg % args if args else msg
                if kwargs:
                    kwargs_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
                    formatted_msg = f"{formatted_msg} | {kwargs_str}"
                print(f"2025-06-29 10:30:15 | CRIT  | {self.name} | {formatted_msg}")

            def configure(self, **kwargs):
                print(f"Mock logger {self.name} configured with {kwargs}")

            def bind(self, **kwargs):
                print(f"Mock logger {self.name} bound with context: {kwargs}")
                return self

            def context(self, name):
                return MockContext(self, name)

        class MockContext:
            def __init__(self, logger, name):
                self.logger = logger
                self.name = name

            def __enter__(self):
                print(f"Entering context: {self.name}")
                return self

            def __exit__(self, *args):
                print(f"Exiting context: {self.name}")

        return MockLogger

    def _create_mock_async_logger(self):
        """Create a mock async logger when LogEverything is not available."""

        class MockAsyncLogger:
            def __init__(self, name=None):
                self.name = name or "mock_async"

            async def debug(self, msg, *args, **kwargs):
                formatted_msg = msg % args if args else msg
                if kwargs:
                    kwargs_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
                    formatted_msg = f"{formatted_msg} | {kwargs_str}"
                print(f"2025-06-29 10:30:15 | DEBUG | {self.name} | {formatted_msg}")

            async def info(self, msg, *args, **kwargs):
                formatted_msg = msg % args if args else msg
                if kwargs:
                    kwargs_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
                    formatted_msg = f"{formatted_msg} | {kwargs_str}"
                print(f"2025-06-29 10:30:15 | INFO  | {self.name} | {formatted_msg}")

            async def warning(self, msg, *args, **kwargs):
                formatted_msg = msg % args if args else msg
                if kwargs:
                    kwargs_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
                    formatted_msg = f"{formatted_msg} | {kwargs_str}"
                print(f"2025-06-29 10:30:15 | WARN  | {self.name} | {formatted_msg}")

            async def error(self, msg, *args, **kwargs):
                formatted_msg = msg % args if args else msg
                if kwargs:
                    kwargs_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
                    formatted_msg = f"{formatted_msg} | {kwargs_str}"
                print(f"2025-06-29 10:30:15 | ERROR | {self.name} | {formatted_msg}")

            async def critical(self, msg, *args, **kwargs):
                formatted_msg = msg % args if args else msg
                if kwargs:
                    kwargs_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
                    formatted_msg = f"{formatted_msg} | {kwargs_str}"
                print(f"2025-06-29 10:30:15 | CRIT  | {self.name} | {formatted_msg}")

            # Sync versions for compatibility
            def info(self, msg, *args, **kwargs):
                formatted_msg = msg % args if args else msg
                if kwargs:
                    kwargs_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
                    formatted_msg = f"{formatted_msg} | {kwargs_str}"
                print(f"2025-06-29 10:30:15 | INFO  | {self.name} | {formatted_msg}")

            # Async methods with 'a' prefix
            async def ainfo(self, msg, *args, **kwargs):
                return await self.info(msg, *args, **kwargs)

            async def adebug(self, msg, *args, **kwargs):
                return await self.debug(msg, *args, **kwargs)

            async def awarning(self, msg, *args, **kwargs):
                return await self.warning(msg, *args, **kwargs)

            async def aerror(self, msg, *args, **kwargs):
                return await self.error(msg, *args, **kwargs)

            async def aexception(self, msg, *args, **kwargs):
                return await self.critical(msg, *args, **kwargs)

            async def configure(self, **kwargs):
                print(f"Mock async logger {self.name} configured with {kwargs}")

            def bind(self, **kwargs):
                print(f"Mock async logger {self.name} bound with context: {kwargs}")
                return self

            def context(self, name):
                return MockAsyncContext(self, name)

        class MockAsyncContext:
            def __init__(self, logger, name):
                self.logger = logger
                self.name = name

            async def __aenter__(self):
                print(f"Entering async context: {self.name}")
                return self

            async def __aexit__(self, *args):
                print(f"Exiting async context: {self.name}")

        return MockAsyncLogger

    def _create_mock_decorator(self):
        """Create a mock decorator when decorators are not available."""

        def mock_decorator(*args, **kwargs):
            def decorator(func_or_class):
                if callable(func_or_class):
                    # It's a function or class, just return it unchanged but log that it would be decorated
                    if hasattr(func_or_class, "__name__"):
                        print(f"# Mock decorator applied to {func_or_class.__name__}")
                    return func_or_class
                return func_or_class

            # Handle both @decorator and @decorator() syntax
            if len(args) == 1 and callable(args[0]) and not kwargs:
                # Direct decoration: @decorator
                return decorator(args[0])
            else:
                # Parametrized decoration: @decorator() or @decorator(params)
                return decorator

        return mock_decorator


def setup(app):
    """Setup the extension."""
    app.add_directive("executable-code", ExecutableCodeDirective)

    # Add CSS for styling the executable code blocks
    app.add_css_file("executable-code.css")

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
