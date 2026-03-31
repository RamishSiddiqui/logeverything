# Getting Started with LogEverything

This directory contains examples to help you get started with LogEverything quickly and easily.

## Examples in this category:

### 1. **basic_usage.py**
- Simple introduction to LogEverything
- Basic logger creation and usage
- Essential logging operations
- Perfect first example to understand the library

### 2. **unified_logger_example.py**
- Demonstrates the clean, simple LogEverything API
- Shows how easy it is to create and use loggers
- Component-specific logging examples
- Ideal for understanding the unified API design

### 3. **modernized_usage.py**
- Showcases the completely modernized LogEverything API (v1.0.0+)
- Demonstrates the simple Logger class and unified @log decorator
- Shows LogEverything's own level constants (DEBUG, INFO, WARNING, etc.)
- High-performance async logging examples
- Great for understanding the modern API improvements

### 4. **hierarchical_imports_example.py**
- Demonstrates the clean, hierarchical import structure
- Shows how to import from different modules (core, decorators, handlers)
- Organized imports for better code structure
- Helpful for understanding the library organization

### 5. **simplified_imports.py**
- Shows the simplest way to import and use LogEverything
- Minimal setup examples
- Quick start patterns
- Perfect for copy-paste into your projects

### 6. **simplified_config_example.py**
- Simple configuration examples
- Basic setup patterns
- Essential configuration options
- Easy configuration management

### 7. **cheatsheet.py**
- Quick reference for common LogEverything operations
- All essential patterns in one place
- Copy-paste ready code snippets
- Perfect quick reference guide

### 8. **simple_visual_alignment.py**
- **NEW!** Simple introduction to LogEverything's visual formatting
- Shows how decorator logs are beautifully aligned and indented
- Perfect for newcomers to see visual benefits immediately
- Beginner-friendly example of function call hierarchy
- Great first example of decorator visual formatting

## Recommended Learning Path:

1. **Start here**: `basic_usage.py` - Learn the fundamentals
2. **Next**: `unified_logger_example.py` - Understand the API design
3. **Then**: `modernized_usage.py` - See the full modern capabilities
4. **Advanced**: `hierarchical_imports_example.py` - Learn proper code organization

## Quick Start:

```python
from logeverything import Logger

# Create a logger
log = Logger("my_app")

# Start logging!
log.info("Hello, LogEverything!")
log.debug("Debug information")
log.warning("Warning message")
log.error("Error occurred")
```

That's it! You're ready to use LogEverything in your projects.

## Next Steps:

After mastering these examples, explore:
- **02_core_features/** - Learn about decorators, handlers, and hierarchy
- **03_async_logging/** - High-performance async logging
- **04_context_managers/** - Advanced context management
- **05_web_frameworks/** - Web application integration
- **06_data_science/** - Data science and ML logging patterns
