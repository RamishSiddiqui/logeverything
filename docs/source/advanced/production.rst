Production Deployment
=====================

This guide covers best practices for deploying LogEverything in production environments, including configuration management, monitoring, scaling, and operational considerations.

Production Architecture
-----------------------

Centralized Logging Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Design a robust logging architecture for production:

.. code-block:: python

    from logeverything import Logger, Profile
    import os
    import json

    class ProductionLoggerFactory:
        """Factory for creating production-ready loggers"""

        def __init__(self, environment="production"):
            self.environment = environment
            self.base_config = self._load_base_config()

        def _load_base_config(self):
            """Load base configuration from environment"""
            return {
                "service_name": os.getenv("SERVICE_NAME", "unknown"),
                "service_version": os.getenv("SERVICE_VERSION", "0.0.0"),
                "environment": self.environment,
                "datacenter": os.getenv("DATACENTER", "unknown"),
                "instance_id": os.getenv("INSTANCE_ID", "unknown")
            }

        def create_logger(self, component_name: str) -> Logger:
            """Create a logger for a specific component"""
            profile = self._create_production_profile(component_name)
            logger = Logger(profile=profile)

            # Add base context to all log messages
            logger.set_default_extra(self.base_config)

            return logger

        def _create_production_profile(self, component_name: str) -> Profile:
            """Create optimized production profile"""
            return Profile(
                name=f"production_{component_name}",
                level=os.getenv("LOG_LEVEL", "INFO"),
                format=self._get_log_format(),
                handlers=self._get_handlers(),
                buffer_size=int(os.getenv("LOG_BUFFER_SIZE", "5000")),
                flush_interval=float(os.getenv("LOG_FLUSH_INTERVAL", "2.0")),
                include_metadata=True,
                compress_logs=True
            )

        def _get_log_format(self):
            """Get structured log format for production"""
            return json.dumps({
                "timestamp": "{timestamp}",
                "level": "{level}",
                "service": "{service_name}",
                "version": "{service_version}",
                "environment": "{environment}",
                "instance": "{instance_id}",
                "component": "{component}",
                "message": "{message}",
                "extra": "{extra}"
            })

        def _get_handlers(self):
            """Configure output handlers based on environment"""
            handlers = ["console"]

            # Add file handler if file logging is enabled
            if os.getenv("LOG_TO_FILE", "false").lower() == "true":
                handlers.append("file")

            # Add remote handlers based on configuration
            if os.getenv("ELASTICSEARCH_URL"):
                handlers.append("elasticsearch")

            if os.getenv("SYSLOG_HOST"):
                handlers.append("syslog")

            return handlers

    # Usage in production
    logger_factory = ProductionLoggerFactory()
    api_logger = logger_factory.create_logger("api")
    db_logger = logger_factory.create_logger("database")
    auth_logger = logger_factory.create_logger("authentication")

Configuration Management
------------------------

Environment-Based Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Manage configuration across different environments:

.. code-block:: python

    import os
    import yaml
    from logeverything import Logger, Profile

    class ConfigurationManager:
        """Manage logging configuration across environments"""

        def __init__(self, config_path="/etc/logeverything"):
            self.config_path = config_path
            self.environment = os.getenv("ENVIRONMENT", "production")
            self.config = self._load_configuration()

        def _load_configuration(self):
            """Load configuration from files and environment"""
            config = {}

            # Load base configuration
            base_config_file = os.path.join(self.config_path, "base.yaml")
            if os.path.exists(base_config_file):
                with open(base_config_file, 'r') as f:
                    config.update(yaml.safe_load(f))

            # Load environment-specific configuration
            env_config_file = os.path.join(self.config_path, f"{self.environment}.yaml")
            if os.path.exists(env_config_file):
                with open(env_config_file, 'r') as f:
                    env_config = yaml.safe_load(f)
                    config = self._deep_merge(config, env_config)

            # Override with environment variables
            config = self._apply_env_overrides(config)

            return config

        def _deep_merge(self, base, override):
            """Deep merge configuration dictionaries"""
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        def _apply_env_overrides(self, config):
            """Apply environment variable overrides"""
            # Map environment variables to config paths
            env_mappings = {
                "LOG_LEVEL": ["default_profile", "level"],
                "LOG_FORMAT": ["default_profile", "format"],
                "LOG_BUFFER_SIZE": ["default_profile", "buffer_size"],
                "LOG_FILE_PATH": ["handlers", "file", "path"],
                "ELASTICSEARCH_URL": ["handlers", "elasticsearch", "url"],
                "SYSLOG_HOST": ["handlers", "syslog", "host"]
            }

            for env_var, config_path in env_mappings.items():
                value = os.getenv(env_var)
                if value:
                    self._set_nested_value(config, config_path, value)

            return config

        def _set_nested_value(self, obj, path, value):
            """Set value in nested dictionary"""
            for key in path[:-1]:
                obj = obj.setdefault(key, {})
            obj[path[-1]] = value

        def get_profile(self, profile_name="default"):
            """Get a configured profile"""
            profile_config = self.config.get("profiles", {}).get(profile_name, {})
            return Profile(name=profile_name, **profile_config)

        def create_logger(self, profile_name="default"):
            """Create a logger with the specified profile"""
            profile = self.get_profile(profile_name)
            return Logger(profile=profile)

**Configuration Files Example:**

**base.yaml:**

.. code-block:: yaml

    profiles:
      default:
        level: INFO
        format: '{"timestamp": "{timestamp}", "level": "{level}", "message": "{message}"}'
        buffer_size: 1000
        flush_interval: 1.0
        handlers: [console]

      api:
        level: INFO
        include_metadata: true
        handlers: [console, file]
        file_path: "/var/log/api.log"

      background_job:
        level: WARNING
        handlers: [console, syslog]

    handlers:
      file:
        rotation: daily
        max_size: 100MB
        backup_count: 7

      syslog:
        facility: local0
        format: structured

**production.yaml:**

.. code-block:: yaml

    profiles:
      default:
        level: WARNING
        buffer_size: 5000
        flush_interval: 5.0
        handlers: [console, elasticsearch]

      api:
        level: INFO
        handlers: [console, file, elasticsearch]

    handlers:
      elasticsearch:
        url: "https://elasticsearch.example.com:9200"
        index_pattern: "logs-{environment}-{date}"
        timeout: 30

Containerized Deployment
------------------------

Docker Configuration
~~~~~~~~~~~~~~~~~~~~

Configure logging for Docker containers:

**Dockerfile:**

.. code-block:: dockerfile

    FROM python:3.11-slim

    # Install LogEverything
    RUN pip install logeverything

    # Create logging directories
    RUN mkdir -p /var/log/app /etc/logeverything

    # Copy configuration
    COPY config/ /etc/logeverything/

    # Copy application
    COPY app/ /app/
    WORKDIR /app

    # Set environment variables
    ENV ENVIRONMENT=production
    ENV LOG_LEVEL=INFO
    ENV LOG_TO_FILE=true
    ENV LOG_FILE_PATH=/var/log/app/app.log

    # Expose log volume
    VOLUME ["/var/log/app"]

    CMD ["python", "main.py"]

**docker-compose.yml:**

.. code-block:: yaml

    version: '3.8'

    services:
      app:
        build: .
        environment:
          - ENVIRONMENT=production
          - LOG_LEVEL=INFO
          - ELASTICSEARCH_URL=http://elasticsearch:9200
        volumes:
          - app-logs:/var/log/app
          - ./config:/etc/logeverything:ro
        depends_on:
          - elasticsearch

      elasticsearch:
        image: elasticsearch:8.5.0
        environment:
          - discovery.type=single-node
          - ES_JAVA_OPTS=-Xms512m -Xmx512m
        volumes:
          - es-data:/usr/share/elasticsearch/data

      kibana:
        image: kibana:8.5.0
        ports:
          - "5601:5601"
        depends_on:
          - elasticsearch

    volumes:
      app-logs:
      es-data:

Kubernetes Deployment
~~~~~~~~~~~~~~~~~~~~~

Deploy with Kubernetes using ConfigMaps and Secrets:

**configmap.yaml:**

.. code-block:: yaml

    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: logeverything-config
    data:
      production.yaml: |
        profiles:
          default:
            level: INFO
            format: '{"timestamp": "{timestamp}", "level": "{level}", "service": "my-service", "message": "{message}"}'
            handlers: [console, elasticsearch]
            buffer_size: 5000
        handlers:
          elasticsearch:
            url: "http://elasticsearch:9200"
            index_pattern: "logs-production-{date}"

**deployment.yaml:**

.. code-block:: yaml

    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: my-app
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: my-app
      template:
        metadata:
          labels:
            app: my-app
        spec:
          containers:
          - name: app
            image: my-app:latest
            env:
            - name: ENVIRONMENT
              value: "production"
            - name: LOG_LEVEL
              value: "INFO"
            - name: INSTANCE_ID
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            volumeMounts:
            - name: config
              mountPath: /etc/logeverything
              readOnly: true
            - name: logs
              mountPath: /var/log/app
          volumes:
          - name: config
            configMap:
              name: logeverything-config
          - name: logs
            emptyDir: {}

Monitoring and Alerting
-----------------------

Health Monitoring
~~~~~~~~~~~~~~~~~

Monitor logging system health:

.. code-block:: python

    import time
    import threading
    from logeverything import Logger

    class LoggingHealthMonitor:
        """Monitor logging system health"""

        def __init__(self, logger: Logger):
            self.logger = logger
            self.metrics = {
                "messages_logged": 0,
                "errors_encountered": 0,
                "buffer_overflows": 0,
                "last_successful_log": time.time()
            }
            self.monitoring = False
            self.monitor_thread = None

        def start_monitoring(self):
            """Start health monitoring"""
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.start()

        def stop_monitoring(self):
            """Stop health monitoring"""
            self.monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join()

        def _monitor_loop(self):
            """Main monitoring loop"""
            while self.monitoring:
                try:
                    # Check logging system health
                    self._check_logging_health()

                    # Report metrics
                    self._report_metrics()

                    time.sleep(60)  # Check every minute

                except Exception as e:
                    print(f"Monitoring error: {e}")

        def _check_logging_health(self):
            """Perform health checks"""
            try:
                # Test log message
                test_message = f"Health check at {time.time()}"
                self.logger.bind(extra={"health_check": True}).info(test_message)

                self.metrics["last_successful_log"] = time.time()
                self.metrics["messages_logged"] += 1

            except Exception as e:
                self.metrics["errors_encountered"] += 1
                print(f"Logging health check failed: {e}")

        def _report_metrics(self):
            """Report health metrics"""
            current_time = time.time()
            time_since_last_log = current_time - self.metrics["last_successful_log"]

            # Alert if logging has been down for too long
            if time_since_last_log > 300:  # 5 minutes
                self._send_alert("Logging system appears to be down")

            # Report metrics to monitoring system
            self._send_metrics({
                "logging.messages_per_minute": self.metrics["messages_logged"],
                "logging.errors_per_minute": self.metrics["errors_encountered"],
                "logging.time_since_last_success": time_since_last_log
            })

            # Reset counters
            self.metrics["messages_logged"] = 0
            self.metrics["errors_encountered"] = 0

        def _send_alert(self, message):
            """Send alert to monitoring system"""
            # Implement your alerting logic here
            print(f"ALERT: {message}")

        def _send_metrics(self, metrics):
            """Send metrics to monitoring system"""
            # Implement your metrics reporting here
            for key, value in metrics.items():
                print(f"METRIC: {key} = {value}")

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~~

Monitor logging performance metrics:

.. code-block:: python

    import time
    import threading
    from collections import defaultdict, deque
    from logeverything import Logger

    class PerformanceMonitor:
        """Monitor logging performance"""

        def __init__(self, logger: Logger):
            self.logger = logger
            self.metrics = defaultdict(lambda: deque(maxlen=1000))
            self.lock = threading.Lock()

        def record_log_operation(self, level, duration, message_size):
            """Record metrics for a log operation"""
            with self.lock:
                timestamp = time.time()
                self.metrics['log_durations'].append((timestamp, duration))
                self.metrics['message_sizes'].append((timestamp, message_size))
                self.metrics['log_counts'].append((timestamp, level))

        def get_performance_stats(self, window_seconds=300):
            """Get performance statistics for the last window"""
            cutoff_time = time.time() - window_seconds

            with self.lock:
                # Filter recent metrics
                recent_durations = [
                    duration for timestamp, duration in self.metrics['log_durations']
                    if timestamp > cutoff_time
                ]

                recent_sizes = [
                    size for timestamp, size in self.metrics['message_sizes']
                    if timestamp > cutoff_time
                ]

                recent_counts = [
                    level for timestamp, level in self.metrics['log_counts']
                    if timestamp > cutoff_time
                ]

            if not recent_durations:
                return {}

            # Calculate statistics
            avg_duration = sum(recent_durations) / len(recent_durations)
            max_duration = max(recent_durations)
            min_duration = min(recent_durations)

            avg_size = sum(recent_sizes) / len(recent_sizes) if recent_sizes else 0

            logs_per_second = len(recent_counts) / window_seconds

            level_counts = defaultdict(int)
            for level in recent_counts:
                level_counts[level] += 1

            return {
                'average_duration_ms': avg_duration * 1000,
                'max_duration_ms': max_duration * 1000,
                'min_duration_ms': min_duration * 1000,
                'average_message_size': avg_size,
                'logs_per_second': logs_per_second,
                'level_distribution': dict(level_counts),
                'total_logs': len(recent_counts)
            }

Scaling Considerations
----------------------

Horizontal Scaling
~~~~~~~~~~~~~~~~~~

Scale logging across multiple instances:

.. code-block:: python

    import hashlib
    import json
    from logeverything import Logger

    class DistributedLogger:
        """Distribute logging across multiple instances"""

        def __init__(self, instances):
            self.instances = instances
            self.loggers = {}

            # Create logger for each instance
            for instance in instances:
                self.loggers[instance] = Logger(
                    profile="distributed",
                    instance_id=instance
                )

        def log(self, level, message, partition_key=None, **kwargs):
            """Log to appropriate instance based on partition key"""
            if partition_key is None:
                partition_key = message

            # Determine target instance using consistent hashing
            instance = self._get_instance(partition_key)
            logger = self.loggers[instance]

            # Add instance info to log
            kwargs['instance'] = instance
            kwargs['partition_key'] = partition_key

            # Log the message
            getattr(logger, level)(message, **kwargs)

        def _get_instance(self, partition_key):
            """Get target instance using consistent hashing"""
            hash_value = hashlib.sha256(str(partition_key).encode()).hexdigest()
            instance_index = int(hash_value, 16) % len(self.instances)
            return self.instances[instance_index]

        def broadcast(self, level, message, **kwargs):
            """Broadcast message to all instances"""
            for logger in self.loggers.values():
                getattr(logger, level)(message, **kwargs)

    # Usage
    distributed_logger = DistributedLogger(['instance-1', 'instance-2', 'instance-3'])

    # Partition by user ID
    distributed_logger.log('info', 'User logged in', partition_key='user_123')

    # Broadcast important messages
    distributed_logger.broadcast('error', 'System error detected')

Load Balancing
~~~~~~~~~~~~~~

Balance logging load across multiple endpoints:

.. code-block:: python

    import random
    import time
    from logeverything import Logger

    class LoadBalancedLogger:
        """Load balance logging across multiple endpoints"""

        def __init__(self, endpoints, strategy='round_robin'):
            self.endpoints = endpoints
            self.strategy = strategy
            self.current_index = 0
            self.endpoint_health = {endpoint: True for endpoint in endpoints}
            self.loggers = {}

            # Create loggers for each endpoint
            for endpoint in endpoints:
                self.loggers[endpoint] = Logger(
                    profile="load_balanced",
                    endpoint=endpoint
                )

        def log(self, level, message, **kwargs):
            """Log using load balancing strategy"""
            endpoint = self._select_endpoint()
            if endpoint:
                logger = self.loggers[endpoint]
                try:
                    getattr(logger, level)(message, **kwargs)
                    self._mark_healthy(endpoint)
                except Exception as e:
                    self._mark_unhealthy(endpoint)
                    # Retry with another endpoint
                    self._retry_log(level, message, **kwargs)

        def _select_endpoint(self):
            """Select endpoint based on strategy"""
            healthy_endpoints = [
                ep for ep in self.endpoints
                if self.endpoint_health[ep]
            ]

            if not healthy_endpoints:
                return None

            if self.strategy == 'round_robin':
                endpoint = healthy_endpoints[self.current_index % len(healthy_endpoints)]
                self.current_index += 1
                return endpoint

            elif self.strategy == 'random':
                return random.choice(healthy_endpoints)

            elif self.strategy == 'least_loaded':
                # Select endpoint with least recent activity
                return min(healthy_endpoints, key=lambda ep: self._get_load(ep))

        def _mark_healthy(self, endpoint):
            """Mark endpoint as healthy"""
            self.endpoint_health[endpoint] = True

        def _mark_unhealthy(self, endpoint):
            """Mark endpoint as unhealthy"""
            self.endpoint_health[endpoint] = False
            # Schedule health check
            threading.Timer(60.0, self._health_check, args=[endpoint]).start()

        def _health_check(self, endpoint):
            """Check if endpoint is healthy again"""
            try:
                logger = self.loggers[endpoint]
                logger.bind(extra={"health_check": True}).info("Health check")
                self._mark_healthy(endpoint)
            except Exception:
                # Still unhealthy, schedule another check
                threading.Timer(60.0, self._health_check, args=[endpoint]).start()

        def _retry_log(self, level, message, **kwargs):
            """Retry logging with different endpoint"""
            endpoint = self._select_endpoint()
            if endpoint:
                try:
                    logger = self.loggers[endpoint]
                    getattr(logger, level)(message, **kwargs)
                    self._mark_healthy(endpoint)
                except Exception:
                    # Log to local fallback
                    print(f"All endpoints failed: {level} - {message}")

Security Considerations
-----------------------

Sensitive Data Handling
~~~~~~~~~~~~~~~~~~~~~~~

Protect sensitive information in logs:

.. code-block:: python

    import re
    import hashlib
    from logeverything import Logger

    class SecureLogger:
        """Logger with built-in security features"""

        def __init__(self):
            self.logger = Logger(profile="secure")
            self.sensitive_patterns = [
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit cards
                r'\b\d{3}-\d{2}-\d{4}\b',                        # SSN
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)',     # Passwords
                r'token["\']?\s*[:=]\s*["\']?([^"\'\s]+)',       # Tokens
            ]

        def log(self, level, message, sanitize=True, **kwargs):
            """Log with automatic sanitization"""
            if sanitize:
                message = self._sanitize_message(message)
                kwargs = self._sanitize_extra(kwargs)

            getattr(self.logger, level)(message, **kwargs)

        def _sanitize_message(self, message):
            """Remove sensitive data from message"""
            sanitized = message

            for pattern in self.sensitive_patterns:
                sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)

            return sanitized

        def _sanitize_extra(self, extra_data):
            """Remove sensitive data from extra fields"""
            sanitized = {}

            for key, value in extra_data.items():
                if self._is_sensitive_field(key):
                    sanitized[key] = self._hash_sensitive_value(value)
                elif isinstance(value, str):
                    sanitized[key] = self._sanitize_message(value)
                else:
                    sanitized[key] = value

            return sanitized

        def _is_sensitive_field(self, field_name):
            """Check if field contains sensitive data"""
            sensitive_fields = [
                'password', 'token', 'secret', 'key', 'credential',
                'ssn', 'social_security', 'credit_card', 'ccn'
            ]

            return any(sensitive in field_name.lower() for sensitive in sensitive_fields)

        def _hash_sensitive_value(self, value):
            """Hash sensitive values for logging"""
            if value is None:
                return None

            # Create SHA256 hash with prefix for identification
            hash_obj = hashlib.sha256(str(value).encode())
            return f"sha256:{hash_obj.hexdigest()[:16]}..."

Access Control
~~~~~~~~~~~~~~

Implement access controls for logging:

.. code-block:: python

    import jwt
    import time
    from functools import wraps
    from logeverything import Logger

    class AccessControlledLogger:
        """Logger with access control"""

        def __init__(self, secret_key):
            self.secret_key = secret_key
            self.logger = Logger(profile="access_controlled")
            self.permissions = {}

        def authenticate(self, token):
            """Authenticate user and return permissions"""
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
                user_id = payload.get('user_id')
                permissions = payload.get('permissions', [])

                self.permissions[user_id] = {
                    'permissions': permissions,
                    'expires': payload.get('exp', time.time() + 3600)
                }

                return user_id
            except jwt.InvalidTokenError:
                return None

        def log_with_auth(self, user_id, level, message, required_permission=None, **kwargs):
            """Log with authentication check"""
            if not self._check_permission(user_id, required_permission):
                self.logger.warning(f"Unauthorized logging attempt by {user_id}")
                return False

            # Add audit information
            kwargs['audit'] = {
                'user_id': user_id,
                'timestamp': time.time(),
                'permission_used': required_permission
            }

            getattr(self.logger, level)(message, **kwargs)
            return True

        def _check_permission(self, user_id, required_permission):
            """Check if user has required permission"""
            if user_id not in self.permissions:
                return False

            user_perms = self.permissions[user_id]

            # Check if permissions expired
            if time.time() > user_perms['expires']:
                del self.permissions[user_id]
                return False

            # Check specific permission
            if required_permission and required_permission not in user_perms['permissions']:
                return False

            return True

Operational Procedures
----------------------

Deployment Checklist
~~~~~~~~~~~~~~~~~~~~

Pre-deployment checklist:

.. code-block:: text

    Configuration:
    [ ] Environment variables configured
    [ ] Profiles validated for target environment
    [ ] Log levels appropriate for environment
    [ ] Output destinations configured and tested
    [ ] Rotation and retention policies set

    Performance:
    [ ] Buffer sizes optimized for expected load
    [ ] Flush intervals configured appropriately
    [ ] Memory limits set and tested
    [ ] Performance benchmarks completed

    Security:
    [ ] Sensitive data sanitization enabled
    [ ] Access controls configured
    [ ] Network security for remote logging
    [ ] Log file permissions set correctly

    Monitoring:
    [ ] Health checks configured
    [ ] Performance metrics collection enabled
    [ ] Alerting rules configured
    [ ] Dashboard setup completed

    Recovery:
    [ ] Backup procedures documented
    [ ] Failover mechanisms tested
    [ ] Recovery procedures documented
    [ ] Emergency contacts updated

Troubleshooting Guide
~~~~~~~~~~~~~~~~~~~~~

Common production issues and solutions:

.. code-block:: python

    from logeverything import Logger
    import psutil
    import os

    class ProductionTroubleshooter:
        """Troubleshoot production logging issues"""

        def __init__(self):
            self.logger = Logger(profile="troubleshooting")

        def diagnose_performance_issues(self):
            """Diagnose performance problems"""
            diagnostics = {}

            # Check system resources
            diagnostics['memory'] = {
                'available_gb': psutil.virtual_memory().available / (1024**3),
                'percent_used': psutil.virtual_memory().percent
            }

            diagnostics['disk'] = {
                'free_gb': psutil.disk_usage('/').free / (1024**3),
                'percent_used': psutil.disk_usage('/').percent
            }

            diagnostics['cpu'] = {
                'percent_used': psutil.cpu_percent(interval=1)
            }

            # Check logging specific metrics
            diagnostics['logging'] = self._check_logging_health()

            self.logger.bind(extra=diagnostics).info("Performance diagnostics")
            return diagnostics

        def _check_logging_health(self):
            """Check logging system health"""
            health = {}

            # Check log file sizes
            log_files = ['/var/log/app.log', '/var/log/error.log']
            for log_file in log_files:
                if os.path.exists(log_file):
                    size_mb = os.path.getsize(log_file) / (1024**2)
                    health[f'{log_file}_size_mb'] = size_mb

            # Check for common issues
            health['issues'] = []

            if psutil.virtual_memory().percent > 90:
                health['issues'].append('High memory usage')

            if psutil.disk_usage('/').percent > 85:
                health['issues'].append('Low disk space')

            return health

Best Practices Summary
----------------------

1. **Configuration Management**: Use environment-specific configurations
2. **Security**: Sanitize sensitive data and implement access controls
3. **Monitoring**: Implement comprehensive health and performance monitoring
4. **Scaling**: Design for horizontal scaling from the start
5. **Error Handling**: Implement robust error handling and fallback mechanisms
6. **Documentation**: Maintain clear operational documentation
7. **Testing**: Test thoroughly in production-like environments
8. **Automation**: Automate deployment and monitoring processes
9. **Security**: Regular security audits and updates
10. **Performance**: Regular performance testing and optimization

API Reference
-------------

Production Classes
~~~~~~~~~~~~~~~~~~

.. py:class:: ProductionLoggerFactory(environment="production")

    Factory for creating production-ready loggers.

    :param environment: Target environment
    :type environment: str

.. py:method:: ProductionLoggerFactory.create_logger(component_name)

    Create a logger for a specific component.

    :param component_name: Name of the component
    :type component_name: str
    :returns: Configured logger
    :rtype: Logger

.. py:class:: ConfigurationManager(config_path="/etc/logeverything")

    Manage logging configuration across environments.

    :param config_path: Path to configuration files
    :type config_path: str

.. py:class:: LoggingHealthMonitor(logger)

    Monitor logging system health.

    :param logger: Logger instance to monitor
    :type logger: Logger
