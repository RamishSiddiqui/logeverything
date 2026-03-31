CLI Tool
========

LogEverything ships a ``logeverything`` console script for quick environment
checks and project scaffolding.  It is also available as
``python -m logeverything``.

The entry point is defined in ``setup.cfg``:

.. code-block:: ini

   [options.entry_points]
   console_scripts =
       logeverything = logeverything.cli:main

version
-------

Print the library version, Python version, and platform:

.. code-block:: console

   $ logeverything version
   logeverything 0.1.0
   Python 3.11.9
   Platform: Windows-10-10.0.26100-SP0

doctor
------

Run a quick diagnostic of your environment.  ``doctor`` checks:

- Python version and platform
- Installed optional packages (``fastapi``, ``celery``, ``orjson``, ``rich``,
  ``psutil``, ``aiohttp``)
- Whether the ``py.typed`` PEP 561 marker is present
- Whether the monitoring dashboard is reachable at ``localhost:8999``
- Number of registered loggers

.. code-block:: console

   $ logeverything doctor
   logeverything doctor
     [+] Python 3.11.9
     [+] Platform: Windows-10-10.0.26100-SP0
     [+] psutil 5.9.5
     [X] celery (not installed)
     [+] orjson 3.10.1
     [+] py.typed marker present
     [X] Dashboard at localhost:8999 (not reachable)
     [+] 0 registered loggers

This is useful after ``pip install -e ".[dev]"`` to verify your environment
is set up correctly.

init
----

Generate a starter ``logging_config.py`` for your project.  The wizard asks
which environment you are targeting:

.. code-block:: console

   $ logeverything init
   LogEverything project initializer

   Select environment type:
     1) web      -- Web application (FastAPI / Flask / Django)
     2) script   -- Standalone script or CLI tool
     3) notebook -- Jupyter notebook

   Enter choice [1/2/3] (default: 2): 1
   Created logging_config.py (web template)

The generated file contains a minimal working configuration you can extend:

.. code-block:: python

   from logeverything import Logger, log

   logger = Logger("app", log_file="app.log", level="INFO")

   @log
   def handle_request(request):
       logger.info("Processing request")

Running via ``python -m``
-------------------------

All commands also work through the module entry point:

.. code-block:: console

   $ python -m logeverything version
   $ python -m logeverything doctor
   $ python -m logeverything init

.. seealso::

   :doc:`../installation`
      How to install LogEverything and optional extras.
