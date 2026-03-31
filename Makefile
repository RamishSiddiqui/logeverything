# Makefile for logeverything project
#
# Usage:
#   make all       - Run clean, format, lint, test, docs, and build in sequence
#   make clean     - Remove build artifacts and cache files
#   make format    - Format code using black and isort
#   make lint      - Check code style and quality
#   make test      - Run tests with coverage
#   make docs      - Build documentation
#   make build     - Build package distribution
#   make release   - Prepare for package release
#   make examples  - Generate example documentation with outputs
#   make benchmark - Run performance benchmarks (summary output only)
#   make benchmark-verbose - Run benchmarks with detailed output
#   make benchmark-MODULE - Run specific benchmark module (e.g., make benchmark-core_logging)
#   make benchmark-MODULE-verbose - Run specific benchmark module with detailed output
#
# Note: This Makefile is cross-platform and works on both Windows and Linux/Mac

.PHONY: all clean lint format test test-verbose docs view-docs build release examples benchmark

# Detect the operating system
ifeq ($(OS),Windows_NT)
	RM_CMD = powershell -c
	RM_DIR = if (Test-Path $(1)) { Remove-Item -Recurse -Force $(1) }
	RM_FILE = if (Test-Path $(1)) { Remove-Item -Force $(1) }
	RM_PATTERN = Get-ChildItem -Path . -Include $(1) -Recurse -Directory | Where-Object { $$_.FullName -notlike '*\.venv\*' } | Remove-Item -Recurse -Force
	DOCS_CMD = powershell -c "cd docs; sphinx-build -b html source build/html"
	VIEW_DOCS_CMD = powershell -c "Start-Process \"file://$(shell powershell -c '$$pwd.Path' | sed 's/\\/\//g')/docs/build/html/index.html\""
else
	RM_CMD = rm -rf
	RM_DIR = $(RM_CMD) $(1)
	RM_FILE = $(RM_CMD) $(1)
	RM_PATTERN = find . -type d -name "$(1)" -not -path "*/.venv/*" -exec rm -rf {} \;
	DOCS_CMD = cd docs && sphinx-build -b html source build/html
	VIEW_DOCS_CMD = xdg-open docs/build/html/index.html || open docs/build/html/index.html
endif

# Main target to run everything
all: clean format lint test docs build

clean:
	$(call RM_DIR,build)
	$(call RM_DIR,dist)
	$(call RM_DIR,*.egg-info)
	$(call RM_DIR,.pytest_cache)
	$(call RM_DIR,.mypy_cache)
	$(call RM_DIR,test_output)
	$(call RM_DIR,.specstory)
	$(call RM_DIR,htmlcov)
	$(call RM_FILE,.coverage)
	$(call RM_FILE,coverage.xml)
	$(call RM_FILE,app.log)
	$(call RM_FILE,logeverything.log)
	$(call RM_FILE,monitoring.db)
	$(call RM_PATTERN,__pycache__)
	$(call RM_PATTERN,.ipynb_checkpoints)
ifeq ($(OS),Windows_NT)
	powershell -c "Get-ChildItem -Path . -Include '*.pyc','*.pyo','*.tmp','*.temp' -Recurse | Remove-Item -Force"
else
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.tmp" -delete
	find . -name "*.temp" -delete
	find . -name "*~" -delete
endif

format:
	black logeverything tests
	isort --profile black logeverything tests

lint:
	flake8 logeverything
	black logeverything tests
	isort --profile black logeverything tests
	mypy logeverything
	bandit -r logeverything

test:
	pytest --cov=logeverything tests/

test-verbose:
	pytest --cov=logeverything tests/ -v

docs:
	$(DOCS_CMD)

examples:
	@echo "Generating examples with outputs..."
	@python tools/generate_markdown_examples.py
	@echo "Examples documentation generated successfully!"
	@echo "To view examples, see docs/source/_examples/examples_with_output.md"
	@echo "To include examples in final documentation, run 'make docs'"

view-docs:
	$(VIEW_DOCS_CMD)

build:
	python -m build

release: clean lint test build
	@echo "Ready to release! Run: twine upload dist/*"

# Benchmark targets
benchmark:
	python benchmarks/run_benchmarks.py

benchmark-verbose:
	python benchmarks/run_benchmarks.py --verbose

benchmark-core_logging:
	python benchmarks/run_benchmarks.py --modules core_logging

benchmark-core_logging-verbose:
	python benchmarks/run_benchmarks.py --modules core_logging --verbose

benchmark-async_logging:
	python benchmarks/run_benchmarks.py --modules async_logging

benchmark-async_logging-verbose:
	python benchmarks/run_benchmarks.py --modules async_logging --verbose

benchmark-context_managers:
	python benchmarks/run_benchmarks.py --modules context_managers

benchmark-context_managers-verbose:
	python benchmarks/run_benchmarks.py --modules context_managers --verbose

benchmark-decorators:
	python benchmarks/run_benchmarks.py --modules decorators

benchmark-decorators-verbose:
	python benchmarks/run_benchmarks.py --modules decorators --verbose

benchmark-external_loggers:
	python benchmarks/run_benchmarks.py --modules external_loggers

benchmark-external_loggers-verbose:
	python benchmarks/run_benchmarks.py --modules external_loggers --verbose

benchmark-print_capture:
	python benchmarks/run_benchmarks.py --modules print_capture

benchmark-print_capture-verbose:
	python benchmarks/run_benchmarks.py --modules print_capture --verbose

benchmark-report:
	python benchmarks/visualize.py --report

benchmark-report-history:
	python benchmarks/visualize.py --report --history

benchmark-compare:
	python benchmarks/compare.py $(MODULE) --baseline 1 --current 0

benchmark-visualize:
	python benchmarks/visualize.py --benchmark $(MODULE) --metric avg_time

benchmark-optimize:
	python benchmarks/optimize.py

benchmark-optimize-report:
	python benchmarks/optimize.py --save benchmarks/results/optimization_report.json

benchmark-test-integration:
	python benchmarks/test_integration.py
