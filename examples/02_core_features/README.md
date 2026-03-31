# Core Features

This directory contains examples demonstrating LogEverything's core features and capabilities.

## Examples in this category:

### 1. **comprehensive_decorators_example.py** ⭐
- Complete guide to all LogEverything decorators
- `@log` (smart auto-detection), `@log_function`, `@log_class`, `@log_io`
- Custom decorator configurations and parameters
- Async function support and exception handling
- **Best comprehensive reference for decorators**

### 2. **logger_hierarchy_example.py** ⭐
- Logger hierarchy system and inheritance
- Configuration inheritance patterns
- Different handlers for different logger levels
- Common logging patterns (module-level, class-based, function-specific)
- Performance-conscious and conditional logging
- **Essential for understanding logger organization**

### 3. **custom_handlers_example.py** ⭐
- Creating custom handlers and formatters
- JSON formatter for structured logging
- Database handler simulation
- Multiple handlers with different levels
- Custom colored formatter with ANSI codes
- **Perfect for advanced handler customization**

### 4. **smart_decorator_example.py**
- Smart unified decorator usage (`@log`)
- Automatic detection of functions, methods, and classes
- Real-world decorator applications
- Decorator best practices

### 5. **decorator_imports_example.py**
- How to import decorators from the decorators module
- Explicit vs. smart decorator usage
- Decorator import patterns and organization

### 6. **visual_formatting_example.py**
- Visual formatting and pretty printing
- Colors, symbols, and indentation
- Theme customization
- Output styling options

### 7. **print_capture_example.py**
- Capturing and redirecting print statements
- Integration with existing codebases
- Print statement logging without code changes

### 8. **decorator_visual_alignment.py** ✨ **NEW!**
- **ENHANCED VISUAL FORMATTING** demonstration
- Shows perfect function entry/exit alignment
- Function body content indented one level deeper
- Professional visual hierarchy for complex nested functions
- Production-ready visual formatting examples
- **Essential for understanding visual alignment improvements**

### 9. **visual_vs_standard_comparison.py** ✨ **NEW!**
- Side-by-side comparison of visual vs standard formatting modes
- Development vs production logging scenarios
- When to use visual formatting vs standard formatting
- Performance and readability trade-offs
- Configuration best practices for different environments
- **Perfect for choosing the right formatting mode**

## Key Concepts Covered:

### Decorators
- **Smart `@log`**: Auto-detects what it's decorating
- **`@log_function`**: Explicit function logging with parameters
- **`@log_class`**: Class-wide logging with method filtering
- **`@log_io`**: I/O operation logging for file operations
- **Custom configurations**: Levels, arguments, results, exception handling

### Logger Hierarchy
- **Parent-child relationships**: `app` → `app.database` → `app.database.queries`
- **Configuration inheritance**: Child loggers inherit parent settings
- **Override capabilities**: Individual loggers can override specific settings
- **Multiple handlers**: Different output destinations per logger

### Custom Handlers
- **Custom formatters**: JSON, colored, structured formats
- **Custom handlers**: Database, file, console, network handlers
- **Handler filtering**: Different log levels for different handlers
- **Resource management**: Automatic cleanup and rotation

### Visual Features
- **Symbols and colors**: Enhanced readability
- **Indentation**: Hierarchical structure visualization
- **Themes**: Light/dark mode support
- **Pretty printing**: Automatic formatting of complex objects

## Recommended Learning Path:

1. **Start with**: `comprehensive_decorators_example.py` - Master all decorators
2. **Essential**: `logger_hierarchy_example.py` - Understand organization
3. **Advanced**: `custom_handlers_example.py` - Learn customization
4. **Specialized**: Other examples based on your specific needs

## Quick Reference:

```python
from logeverything import Logger
from logeverything.decorators import log, log_function, log_class, log_io

# Smart decorator (auto-detects)
@log
def my_function():
    pass

@log
class MyClass:
    pass

# Explicit decorators
@log_function(level="DEBUG", include_args=True, include_result=True)
def detailed_function(x, y):
    return x + y

@log_class(level="INFO", include_private=False)
class BusinessLogic:
    def public_method(self):
        pass

    def _private_method(self):  # Not logged
        pass

@log_io(level="INFO", log_args=True)
def file_operation(filename):
    with open(filename, 'r') as f:
        return f.read()

# Logger hierarchy
app_logger = Logger("myapp")
db_logger = Logger("myapp.database")  # Inherits from app_logger
cache_logger = Logger("myapp.cache")  # Inherits from app_logger
```

## Next Steps:

After mastering core features, explore:
- **03_async_logging/** - High-performance async patterns
- **04_context_managers/** - Advanced context management
- **05_web_frameworks/** - Web application integration
