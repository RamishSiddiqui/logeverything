Installation
============

System Requirements
-------------------

LogEverything supports:

- **Python 3.8+** (3.8, 3.9, 3.10, 3.11, 3.12)
- **Operating Systems**: Windows, macOS, Linux
- **Architectures**: x86_64, ARM64

Core Installation
-----------------

Install LogEverything with pip:

.. code-block:: bash

   pip install logeverything

This installs the core library with minimal dependencies (only ``colorama`` for cross-platform color support).

Feature-Specific Installations
-------------------------------

LogEverything provides optional dependencies for specific features:

**Web Framework Support**

.. code-block:: bash

   # FastAPI integration
   pip install "logeverything[fastapi]"

   # Flask integration
   pip install "logeverything[flask]"

   # Django integration
   pip install "logeverything[django]"

   # All web frameworks
   pip install "logeverything[web]"

**Enhanced Visual Output**

.. code-block:: bash

   # Rich text formatting and image support
   pip install "logeverything[visual]"

**Machine Learning & Data Science**

.. code-block:: bash

   # MLflow, pandas, numpy integration
   pip install "logeverything[ml]"

**Cloud & Database Integration**

.. code-block:: bash

   # Cloud providers (AWS, GCP, Azure)
   pip install "logeverything[cloud]"

   # Database logging
   pip install "logeverything[db]"

**High-Performance JSON**

.. code-block:: bash

   # Fast JSON serialization with orjson
   pip install "logeverything[json]"

**Complete Installation**

.. code-block:: bash

   # All features (except development tools)
   pip install "logeverything[full]"

Development Installation
------------------------

For contributing or advanced usage:

.. code-block:: bash

   # Development tools (testing, linting, docs)
   pip install "logeverything[dev]"

From Source
-----------

Install the latest development version:

.. code-block:: bash

   pip install git+https://github.com/logeverything/logeverything.git

Or clone and install locally:

.. code-block:: bash

   git clone https://github.com/logeverything/logeverything.git
   cd logeverything
   pip install -e ".[dev]"

Verification
------------

Verify your installation:

.. executable-code::

   import logeverything

   # Check version
   print(f"LogEverything version: {logeverything.__version__}")

   # Quick test
   log = logeverything.Logger("test")
   log.info("Installation successful!")

Upgrading
---------

Upgrade to the latest version:

.. code-block:: bash

   pip install --upgrade logeverything

Dependencies
------------

**Core Dependencies:**

- ``colorama>=0.4.4`` - Cross-platform color support

**Optional Dependencies by Feature:**

.. list-table::
   :header-rows: 1

   * - Feature
     - Dependencies
     - Installation
   * - Web Frameworks
     - fastapi, flask, django, starlette
     - ``pip install "logeverything[web]"``
   * - Visual Enhancement
     - rich, pillow
     - ``pip install "logeverything[visual]"``
   * - Machine Learning
     - mlflow, numpy, pandas
     - ``pip install "logeverything[ml]"``
   * - Fast JSON
     - orjson
     - ``pip install "logeverything[json]"``
   * - Cloud Integration
     - boto3, google-cloud-logging, azure-monitor
     - ``pip install "logeverything[cloud]"``

Troubleshooting
---------------

**Common Issues:**

**Import Error**
   Ensure you're using Python 3.8 or later:

   .. code-block:: bash

      python --version

**Color Issues on Windows**
   LogEverything automatically handles Windows console colors. If you experience issues:

   .. code-block:: python

      from logeverything import Logger
      log = Logger()
      log.configure(disable_colors=True)  # Disable colors if needed

**Unicode Symbol Issues on Windows**
   LogEverything automatically fixes Unicode encoding issues on Windows. All fixes are applied automatically:

   * **File handlers use UTF-8 encoding** by default (prevents ``cp1252`` codec errors)
   * **Smart symbol fallback** converts Unicode symbols to ASCII alternatives when needed
   * **Platform detection** automatically adjusts for Windows console capabilities

   Manual override (rarely needed):

   .. code-block:: python

      from logeverything import Logger
      log = Logger()
      log.configure(
          use_symbols=False,     # Disable Unicode symbols
          visual_mode=True       # Keep visual formatting
      )

   **Symbol fallback mapping**: 🔍→[D], ℹ️→[I], ⚠️→[W], ❌→[E], ✅→[OK], 🔵→[CALL]

**Performance Issues**
   For maximum performance in production:

   .. code-block:: python

      from logeverything import Logger
      log = Logger()
      log.configure(
          profile="production",  # Optimized settings
          level="WARNING"        # Reduce log volume
      )

Need Help?
----------

- **Documentation**: https://logeverything.readthedocs.io/
- **GitHub Issues**: https://github.com/logeverything/logeverything/issues
- **Discussions**: https://github.com/logeverything/logeverything/discussions
