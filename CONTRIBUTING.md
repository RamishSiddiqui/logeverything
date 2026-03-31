# Contributing to LogEverything

Thank you for your interest in contributing to LogEverything! This document provides guidelines and instructions to help you get started.

## Development Environment Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/logeverything.git
   cd logeverything
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
   This will install the package in development mode with all the required dependencies.

4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```
   This will install Git hooks in your local repository that will automatically check your code before each commit.

5. Create a branch for your feature:
   ```bash
   git checkout -b feature-name
   ```
   Use a descriptive name that reflects your contribution (e.g., `add-json-formatting`, `fix-windows-encoding`).

## Code Style and Quality Standards

We follow these standards to maintain code quality:

- **Code Formatting**: We use [Black](https://black.readthedocs.io/) with a line length of 100 characters.
- **Import Sorting**: We use [isort](https://pycqa.github.io/isort/) with Black compatibility.
- **Linting**: We use [flake8](https://flake8.pycqa.org/) for code linting.
- **Type Checking**: We use [mypy](https://mypy.readthedocs.io/) for static type checking.
- **Security**: We use [bandit](https://bandit.readthedocs.io/) for security vulnerability checks.

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality standards are met before code is committed. The hooks will:

- Check for trailing whitespace and fix it
- Ensure files end with a newline
- Verify YAML files are valid
- Check for large files that shouldn't be committed
- Remove Python debug statements
- Format code with Black
- Sort imports with isort
- Check code with flake8
- Run type checking with mypy
- Perform security scanning with bandit

If a hook fails, the commit will be aborted. You can run the hooks manually at any time:

```bash
pre-commit run --all-files  # Run on all files
pre-commit run  # Run only on staged files
```

Some issues can be fixed automatically by the hooks, and some will require manual fixing. When pre-commit fixes issues automatically, you'll need to stage the changes before committing again.

You can also run individual quality checks using the Makefile:

```bash
make lint  # Check all quality standards
make format  # Auto-format code with Black and isort
```

Before submitting a pull request, make sure all checks pass with:

```bash
make all  # Runs clean, format, lint, test, docs, and build
```

## Testing

All new features should include tests. We use [pytest](https://docs.pytest.org/) for testing:

```bash
make test  # Run all tests
make test-verbose  # Run tests with verbose output
```

To check code coverage:

```bash
pytest --cov=logeverything tests/  # Generate coverage report
```

Testing requirements:

- At least 90% line coverage for new features
- All edge cases should be tested
- Both success and failure paths should be verified
- Cross-platform compatibility should be tested

When adding visual features, use the `test_visual_output.py` module to verify the output format.

## Documentation

All new features should include documentation:

1. **Docstrings**: Add Google-style docstrings to all public functions, classes, and methods:
   ```python
   def example_function(param1: str, param2: int = 10) -> bool:
       """
       Short description of the function.

       Longer description explaining the behavior in detail.

       Args:
           param1: Description of param1
           param2: Description of param2, with default value

       Returns:
           Description of the return value

       Raises:
           ValueError: When param1 is empty
           TypeError: When param2 is not an integer

       Example:
           >>> example_function("test", 5)
           True
       """
   ```

2. **Examples**: Include usage examples in docstrings and update the examples directory if needed.
3. **Type Hints**: Use Python type hints for all function signatures.
4. **Sphinx Docs**: Update Sphinx documentation when adding new features.

Build and check the documentation:

```bash
make docs  # Build docs
make view-docs  # View docs in browser
make examples  # Generate example documentation with outputs
```

## Architecture Overview

When contributing new features, please be mindful of our architecture:

1. **Core Module** (`core.py`): Contains the central logging functionality
2. **Decorators** (`decorators.py`): Provides function/class decorators for logging
3. **Handlers** (`handlers.py`): Custom log handlers for different outputs
4. **Print Capture** (`print_capture.py`): Utilities for capturing print statements

New features should follow this separation of concerns and extend the appropriate modules.

## Version Control Guidelines

### Files to Exclude from Version Control

The repository includes a `.gitignore` file that automatically excludes the following types of files:

- **Python cache files**: `__pycache__/`, `*.py[cod]`, `*$py.class`
- **Build artifacts**: `dist/`, `build/`, `*.egg-info/`, `wheels/`
- **IDE settings**: `.idea/`, `.vscode/`
- **Testing artifacts**: `.coverage*`, `htmlcov/`, `.pytest_cache/`, `coverage.xml`
- **Virtual environments**: `.env`, `.venv`, `env/`, `venv/`
- **Documentation builds**: `docs/build/`, generated example outputs
- **Local testing output**: `test_output/`
- **Log files**: `*.log`

If you add new types of generated files or temporary artifacts to the project, please update the `.gitignore` file accordingly.

When adding files to your commits, run `git status` before committing to ensure you're not including any files that should be excluded.

### Pull Request Process

1. Ensure your code passes all tests, linting, and type checks.
2. Update documentation as needed.
3. Update CHANGELOG.md with details of your changes under the "Unreleased" section.
4. Submit a pull request to the main repository.
5. Ensure the CI pipeline passes.
6. Address any feedback from code reviews.
7. Once approved, a maintainer will merge your PR.

## Commit Message Guidelines

Please follow these guidelines for commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line
- Consider starting the commit message with an applicable emoji:
  - ✨ (sparkles) for new features
  - 🐛 (bug) for bug fixes
  - 📚 (books) for documentation changes
  - ♻️ (recycle) for refactoring
  - 🧪 (test tube) for adding tests
  - 🚀 (rocket) for performance improvements
  - 🔒 (lock) for security fixes

Example:
```
✨ Add color theme support for console output

Implement multiple color themes (default, bold, pastel, monochrome) for
the EnhancedConsoleHandler with configurable settings.

Closes #42
```

## Versioning System

LogEverything follows [Semantic Versioning](https://semver.org/) (SemVer). Version numbers are formatted as `MAJOR.MINOR.PATCH` (e.g., v1.2.4):

1. **MAJOR version (1)**: Incremented for incompatible API changes
   - Breaking changes that require user code modifications
   - Removal of deprecated features
   - Major architectural changes

2. **MINOR version (2)**: Incremented for added functionality in a backward compatible manner
   - New features
   - New public APIs
   - Deprecation notices for future breaking changes

3. **PATCH version (4)**: Incremented for backward compatible bug fixes
   - Bug fixes
   - Performance improvements
   - Documentation updates
   - Internal refactoring with no API changes

Examples:
- v1.2.4 → v1.2.5: Bug fix release
- v1.2.4 → v1.3.0: New feature release
- v1.2.4 → v2.0.0: Breaking change release

## Release Process

Releases are automated via GitHub Actions. When a version tag is pushed, CI runs the
test suite, builds the package, creates a GitHub Release with the changelog and build
artifacts attached, and publishes to PyPI via Trusted Publisher (OIDC).

### What maintainers do

1. Update version in `logeverything/__init__.py`:
   ```python
   __version__ = "1.2.4"  # Update to new version
   ```

2. Update `CHANGELOG.md`:
   - Move items from "Unreleased" into a new versioned heading (e.g., `## [1.2.4] - 2026-02-24`)
   - Add a fresh empty "Unreleased" section at the top

3. Commit, tag, and push:
   ```bash
   git add logeverything/__init__.py CHANGELOG.md
   git commit -m "Release v1.2.4"
   git tag v1.2.4
   git push origin main v1.2.4
   ```

### What CI does automatically

Once the `v*` tag is pushed, the `release.yml` workflow:

1. Runs the full test suite (gates the release on passing tests)
2. Builds the package (`wheel` + `sdist`) and extracts the changelog section
3. **Pauses for maintainer approval** — the `publish` job uses the `release` environment, which requires a designated reviewer to approve before proceeding
4. Creates a GitHub Release with the changelog as the body and `dist/*` as attached assets
5. Publishes to PyPI via Trusted Publisher (OIDC — no API tokens required)

> **Setup:** To enable the approval gate, go to **Settings > Environments > release**
> and add yourself as a required reviewer. This ensures only you can authorize the
> publish step, even if someone else pushes a tag.

### Dashboard releases

Dashboard releases follow the same pattern with `dashboard-v*` tags:

```bash
git tag dashboard-v0.1.0
git push origin dashboard-v0.1.0
```

The `dashboard-release.yml` workflow builds the dashboard package from
`logeverything-dashboard/`, creates a GitHub Release, and publishes to PyPI.
It uses the same `release` environment approval gate.

Only project maintainers handle the release process.

## Questions?

If you have any questions or need help, please:

- Open an issue on GitHub
- Join our community discussions
- Check existing documentation

Thank you for contributing to LogEverything!
