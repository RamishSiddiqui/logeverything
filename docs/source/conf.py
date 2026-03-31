"""
Configuration file for the Sphinx documentation builder.
"""
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))
sys.path.insert(0, os.path.abspath("_extensions"))  # Add extensions directory

# -- Project information -----------------------------------------------------
project = "LogEverything"
copyright = "2025-2026, LogEverything Team"
author = "Muhammad Ramish Siddiqui"

# The full version, including alpha/beta/rc tags
from logeverything import __version__ as release  # noqa: E402

# Project title and tagline for Furo
html_title = "LogEverything"
html_short_title = "LogEverything"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "myst_parser",  # Add MyST parser for markdown support
    "executable_code",  # Our custom extension for executable code blocks
]

# MyST parser settings
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"  # Modern, clean Furo theme
html_static_path = ["_static"]

# Custom CSS and JS files
html_css_files = [
    "custom.css",
]

html_js_files = [
    "custom.js",
]

# Theme options (Furo theme options)
html_theme_options = {
    "sidebar_hide_name": True,
    "light_css_variables": {
        "color-brand-primary": "#2563eb",
        "color-brand-content": "#2563eb",
        "font-stack": "'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
        "font-stack--monospace": "'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace",
    },
    "dark_css_variables": {
        "color-brand-primary": "#60a5fa",
        "color-brand-content": "#60a5fa",
        "font-stack": "'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
        "font-stack--monospace": "'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace",
    },
    "source_repository": "https://github.com/RamishSiddiqui/logeverything",
    "source_branch": "main",
    "source_directory": "docs/",
}

html_meta = {
    "description": "LogEverything — high-performance Python logging with decorators, async support, structured JSON output, and a monitoring dashboard.",
    "keywords": "python logging, decorator logging, async logging, structured logging, json logging, log rotation, monitoring dashboard, function tracing, observability",
    "og:title": "LogEverything Documentation",
    "og:description": "High-performance Python logging with decorators, async support, structured JSON output, and a companion monitoring dashboard.",
    "og:type": "website",
}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# -- Extension configuration -------------------------------------------------

# Mock imports that may not be available in the docs build environment
autodoc_mock_imports = ["psutil", "fastapi", "uvicorn", "starlette", "flask", "django", "celery"]

# Suppress ambiguous cross-reference warnings (Logger is re-exported at package level)
suppress_warnings = ["ref.python"]

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}
