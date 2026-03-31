"""
Framework integrations for LogEverything.

Provides middleware and extensions for popular Python web frameworks and
task queues. All framework imports are guarded — no framework is a required
dependency.

Available integrations:
- ASGI (FastAPI, Starlette, Quart)
- WSGI (Flask, Django, Bottle)
- FastAPI (Depends-based request logger)
- Flask (extension with factory pattern)
- Django (standard middleware protocol)
- Celery (signal-based task logging)
"""
