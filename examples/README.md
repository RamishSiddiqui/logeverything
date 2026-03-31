# LogEverything Examples

This directory contains comprehensive examples demonstrating all features of the LogEverything library, including the **new enhanced visual alignment capabilities**! Examples are organized by category and complexity level to help you find exactly what you need.

## ✨ **NEW! Enhanced Visual Alignment**

LogEverything now features **dramatically improved visual formatting** with perfect function entry/exit alignment and intelligent indentation. Check out these new examples:

- 🎯 **01_getting_started/simple_visual_alignment.py** - Beautiful visual formatting for beginners
- 🎨 **02_core_features/decorator_visual_alignment.py** - Professional visual hierarchy demonstration
- 📊 **02_core_features/visual_vs_standard_comparison.py** - When to use visual vs standard formatting
- 🚀 **08_advanced/multi_level_visual_alignment.py** - Complex scenarios with deep nesting

**Key Visual Improvements:**
- ✅ Function entry and exit logs are perfectly aligned at each level
- ✅ Function body content is automatically indented one level deeper
- ✅ Clear visual hierarchy makes debugging complex code effortless
- ✅ Conditional emoji usage based on configuration
- ✅ Production-ready formatting suitable for enterprise use

## 📁 Directory Structure

### 01_getting_started/
Basic examples for new users getting started with LogEverything.
- `hello_world.py` - Your first LogEverything program
- `basic_configuration.py` - Simple logging setup
- `quick_start.py` - 5-minute quick start guide
- `simple_visual_alignment.py` - Beautiful visual formatting for beginners

### 02_core_features/
Core functionality and essential features.
- `logger_basics.py` - Logger class fundamentals
- `configuration_options.py` - All configuration options
- `handlers_and_formatters.py` - Custom handlers and formatters
- `log_levels.py` - Working with different log levels
- `print_capture.py` - Capturing print statements
- `decorator_visual_alignment.py` - Professional visual hierarchy demonstration
- `visual_vs_standard_comparison.py` - When to use visual vs standard formatting

### 03_async_logging/
Async/await support and async logging patterns.
- `async_logger_basics.py` - AsyncLogger fundamentals
- `async_context_managers.py` - Async context managers
- `async_performance.py` - Performance-optimized async logging
- `async_web_server.py` - Async web server logging

### 04_context_managers/
Context managers for scoped logging.
- `logging_contexts.py` - Basic context managers
- `performance_contexts.py` - Performance monitoring contexts
- `visual_contexts.py` - Visual logging with emojis
- `nested_contexts.py` - Complex nested contexts

### 05_web_frameworks/
Integration with popular web frameworks.
- `django_integration.py` - Django project integration
- `flask_integration.py` - Flask application logging
- `fastapi_integration.py` - FastAPI async logging
- `tornado_integration.py` - Tornado async framework

### 06_data_science/
Data science and machine learning logging.
- `pandas_logging.py` - DataFrame and data processing
- `jupyter_notebook.py` - Jupyter notebook integration
- `model_training.py` - ML model training logging
- `experiment_tracking.py` - Scientific experiment logging

### 07_integrations/
Third-party library integrations.
- `external_loggers.py` - Integrating with other loggers
- `common_libraries.py` - Popular library configurations
- `monitoring_systems.py` - Integration with monitoring tools
- `log_aggregation.py` - Log aggregation patterns

### 08_advanced/
Advanced features and patterns.
- `custom_handlers.py` - Building custom handlers
- `performance_optimization.py` - Performance tuning
- `security_logging.py` - Security-focused logging
- `distributed_logging.py` - Multi-process/distributed systems
- `multi_level_visual_alignment.py` - Complex scenarios with deep nesting

### 09_migration/
Migration guides and compatibility.
- `from_standard_logging.py` - Migrating from Python logging
- `api_migration.py` - Migrating from older LogEverything versions
- `legacy_compatibility.py` - Backward compatibility examples

## 🆕 Stand-Alone Examples

### decorator_enhancement_examples.py
**NEW in v1.0.0** - Comprehensive demonstration of the enhanced decorator system:
- Smart logger selection with the `using` parameter
- Automatic logger discovery and registration
- Error handling with helpful guidance messages
- Multi-tier application logging patterns
- Performance monitoring integration
- Real-world usage scenarios

Run this example to see all the new decorator features in action:
```bash
python examples/decorator_enhancement_examples.py
```

### unified_logger_example.py

## 🚀 Quick Start

1. **Brand New?** Start with `01_getting_started/hello_world.py`
2. **Need Basic Logging?** Check `02_core_features/logger_basics.py`
3. **Using Async?** Jump to `03_async_logging/async_logger_basics.py`
4. **Web Development?** Browse `05_web_frameworks/`
5. **Data Science?** Explore `06_data_science/`

## 💡 Example Naming Convention

- `*_basics.py` - Fundamental concepts
- `*_advanced.py` - Advanced usage patterns
- `*_integration.py` - Framework/library integration
- `*_performance.py` - Performance-focused examples
- `*_real_world.py` - Real-world scenarios

## 🔧 Running Examples

All examples are self-contained and can be run directly:

```bash
# Run any example
python examples/01_getting_started/hello_world.py

# Run with different log levels
LOGLEVEL=DEBUG python examples/02_core_features/logger_basics.py
```

## 📖 Documentation

Each example includes:
- Comprehensive docstrings explaining the concepts
- Inline comments for complex sections
- Expected output examples
- Links to relevant documentation

## 🤝 Contributing

When adding new examples:
1. Place them in the appropriate category directory
2. Follow the naming convention
3. Include comprehensive documentation
4. Add to this README if creating new categories
5. Ensure examples are self-contained and runnable

## 📚 Additional Resources

- [Official Documentation](../docs/)
- [API Reference](../docs/api/)
- [Migration Guide](../docs/migration.rst)
- [Performance Guide](../docs/performance.rst)
