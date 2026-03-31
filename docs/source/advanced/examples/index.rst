Production Examples
===================

This section contains real-world, production-grade examples that demonstrate LogEverything's capabilities in complex business environments. These examples showcase intelligent type casting, advanced async/sync integration, and robust logging patterns suitable for enterprise applications.

.. toctree::
   :maxdepth: 2
   :caption: Example Categories

   async-microservices

Overview
--------

Our production examples are organized by category to help you find relevant patterns for your use case:

**Async Microservices**
   Complex service architectures with mixed async/sync operations, database integration, external APIs, and concurrent processing.

**Data Processing Pipelines** *(Coming Soon)*
   High-throughput batch processing, ETL workflows, and stream processing with comprehensive monitoring.

**Web Applications** *(Coming Soon)*
   Real-time web services, API gateways, authentication systems, and request/response logging.

**ML/AI Systems** *(Coming Soon)*
   Model training pipelines, inference services, and experiment tracking with detailed metrics.

**Monitoring & Observability** *(Coming Soon)*
   Health checks, performance monitoring, alerting systems, and log analysis patterns.

Key Features Demonstrated
-------------------------

All examples in this section demonstrate:

**🔄 Intelligent Type Casting**
   The same ``@log`` decorator seamlessly handles both async and sync methods without configuration.

**🏗️ Production Architecture**
   Real-world service patterns with proper error handling, resource management, and scalability considerations.

**⚡ Performance Monitoring**
   Built-in timing metrics, call tracking, and performance optimization opportunities.

**🛡️ Error Handling**
   Comprehensive error tracking, retry mechanisms, and graceful degradation patterns.

**📊 Observability**
   Structured logging, context propagation, and monitoring-ready output formats.

**🚀 Scalability**
   Concurrent processing, resource pooling, and high-throughput design patterns.

Usage Guidelines
----------------

Each example includes:

- **Complete source code** with inline documentation
- **Architecture overview** explaining the design decisions
- **Key features highlighted** with explanations of type casting behavior
- **Sample output** showing the logging behavior
- **Adaptation tips** for customizing to your specific needs

.. note::
   These examples are designed as reference implementations. They include
   realistic complexity but may need adaptation for your specific production
   requirements. Focus on the logging patterns and type casting behavior
   rather than the business logic details.

.. tip::
   Start with the async microservices example if you're working with:

   - Multi-service architectures
   - Database and external API integrations
   - Mixed async/sync operations
   - Concurrent processing requirements
   - Complex error handling needs
