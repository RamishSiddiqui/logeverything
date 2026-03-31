"""
Log transport for LogEverything.

Network transports that ship structured log records from application processes
to the dashboard or any central collector.  Each transport is a
``logging.Handler`` subclass — just add it to any logger's handler list.

Available transports:
- HTTPTransportHandler (stdlib urllib, zero external deps)
- TCPTransportHandler (persistent TCP, newline-delimited JSON)
- UDPTransportHandler (fire-and-forget UDP datagrams)
"""
