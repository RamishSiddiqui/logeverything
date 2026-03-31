"""
Setup script for the LogEverything package.
"""

import os
import re

from setuptools import find_packages, setup

# Read the version from __init__.py
with open(os.path.join("logeverything", "__init__.py"), "r", encoding="utf-8") as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
    version = version_match.group(1) if version_match else "0.1.0"

# Read long description from README file
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="logeverything",
    version=version,
    description="A comprehensive logging library for Python applications with minimal code changes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Muhammad Ramish Siddiqui",
    author_email="",
    url="https://github.com/RamishSiddiqui/logeverything",
    packages=find_packages(exclude=["tests", "docs", "examples", "tools"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
    ],
    python_requires=">=3.7",
    install_requires=[
        "colorama>=0.4.4",  # Minimal dependency for cross-platform color support
    ],
    extras_require={
        # Development and testing tools
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-xdist>=3.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "flake8-docstrings>=1.7.0",  # Added for better docstring checks
            "isort>=5.10.0",
            "mypy>=0.971",
            "bandit>=1.7.0",
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "sphinx-autodoc-typehints>=1.18.0",
            "myst-parser>=1.0.0",  # Added from requirements.txt
            "build>=0.8.0",
            "twine>=4.0.0",
            "wheel>=0.38.0",
            "pre-commit>=3.3.2",  # Added for git hooks
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-xdist>=3.0.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "sphinx-autodoc-typehints>=1.18.0",
            "myst-parser>=1.0.0",  # Added from requirements.txt
        ],
        # Feature-specific dependencies
        "full": [  # All features (except dev tools)
            "rich>=10.0.0",  # Enhanced terminal output
            "orjson>=3.5.0",  # Fast JSON serialization
            "fastapi>=0.68.0",  # FastAPI integration
            "requests>=2.25.0",  # HTTP logging
            "sqlalchemy>=1.4.0",  # Database logging
            "pydantic>=1.8.0",  # Data validation
            "prometheus-client>=0.12.0",  # Metrics export
            "elasticsearch>=7.0.0",  # ELK stack integration
            "mlflow>=1.0.0",  # MLflow integration
            "pillow>=9.0.0",  # Image logging support
        ],
        "web": [  # Web framework integrations
            "fastapi>=0.68.0",  # FastAPI integration
            "starlette>=0.14.0",  # Starlette/FastAPI middleware
            "flask>=2.0.0",  # Flask integration
            "django>=3.2.0",  # Django integration
        ],
        "fastapi": [  # FastAPI-specific integration
            "fastapi>=0.68.0",
            "starlette>=0.14.0",
        ],
        "flask": ["flask>=2.0.0"],  # Flask integration
        "django": ["django>=3.2.0"],  # Django integration
        "visual": [  # Enhanced visual formatting
            "rich>=10.0.0",  # Rich text and formatting
            "pillow>=9.0.0",  # Image support
        ],
        "json": ["orjson>=3.5.0"],  # Fast JSON processing
        "db": ["sqlalchemy>=1.4.0"],  # Database logging
        "metrics": ["prometheus-client>=0.12.0"],  # Metrics export
        "ml": [  # Machine learning integrations
            "mlflow>=1.0.0",  # MLflow integration
            "numpy>=1.20.0",  # Numerical data
            "pandas>=1.3.0",  # DataFrame logging
        ],
        "cloud": [  # Cloud integrations
            "boto3>=1.17.0",  # AWS integration
            "google-cloud-logging>=2.0.0",  # GCP integration
            "azure-monitor-opentelemetry>=1.0.0",  # Azure integration
        ],
    },
    project_urls={
        "Documentation": "https://logeverything.readthedocs.io/",
        "Source": "https://github.com/logeverything/logeverything",
        "Tracker": "https://github.com/logeverything/logeverything/issues",
    },
    keywords="logging, log, debug, tracing, performance, monitoring, visualization, hierarchical, decorators",
    entry_points={
        "console_scripts": [
            # Add any command-line scripts here if needed
            # 'logeverything-cli=logeverything.cli:main',
        ],
    },
)
