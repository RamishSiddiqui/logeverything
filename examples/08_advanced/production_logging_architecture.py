#!/usr/bin/env python3
"""
Production-Ready Logging Architecture Example

This example demonstrates a comprehensive, production-ready logging setup
using LogEverything, including:
- Multi-environment configuration
- Centralized logging architecture
- Log aggregation and filtering
- Security and compliance logging
- Performance monitoring
- Alert integration
- Log rotation and archival
"""

import asyncio
import sys
import threading
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from logeverything import AsyncLogger, Logger, configure
from logeverything.decorators import log
from logeverything.handlers import (
    ConsoleHandler,
    FileHandler,
    JSONLineFormatter,
    TimedRotatingFileHandler,
)


class Environment(Enum):
    """Application environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(Enum):
    """Extended log levels for different scenarios."""

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SECURITY = "SECURITY"
    AUDIT = "AUDIT"


class LoggingConfiguration:
    """Centralized logging configuration manager."""

    def __init__(self, environment: Environment):
        self.environment = environment
        self.config = self._get_environment_config()
        self.logger = Logger("logging_config")

    def _get_environment_config(self) -> Dict[str, Any]:
        """Get configuration based on environment."""
        base_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "backup_count": 10,
            "compression": True,
        }

        if self.environment == Environment.DEVELOPMENT:
            return {
                **base_config,
                "level": "DEBUG",
                "console_logging": True,
                "file_logging": True,
                "structured_logging": False,
                "performance_monitoring": True,
                "security_logging": False,
            }

        elif self.environment == Environment.STAGING:
            return {
                **base_config,
                "level": "INFO",
                "console_logging": True,
                "file_logging": True,
                "structured_logging": True,
                "performance_monitoring": True,
                "security_logging": True,
                "log_aggregation": True,
            }

        elif self.environment == Environment.PRODUCTION:
            return {
                **base_config,
                "level": "WARNING",
                "console_logging": False,
                "file_logging": True,
                "structured_logging": True,
                "performance_monitoring": True,
                "security_logging": True,
                "log_aggregation": True,
                "compliance_logging": True,
                "alert_integration": True,
            }

    def apply_configuration(self):
        """Apply logging configuration."""
        self.logger.info(f"Applying {self.environment.value} logging configuration")

        configure(
            level=self.config["level"],
            visual_mode=self.config.get("console_logging", False),
            use_symbols=True,
            format_type="detailed" if self.config.get("structured_logging") else "simple",
        )

        self.logger.info("Logging configuration applied successfully")

    def create_production_logger(self, name: str) -> Logger:
        """Create a logger with rotation handlers appropriate for this environment.

        In production: JSONL with daily rotation + compressed archives.
        In development: plain-text file + console.
        """
        logger = Logger(name, auto_setup=False)

        if self.config.get("console_logging"):
            console = ConsoleHandler()
            console.setLevel(
                logging.DEBUG if self.environment == Environment.DEVELOPMENT else logging.INFO
            )
            logger.add_handler(console)

        if self.config.get("structured_logging"):
            # Structured JSONL with daily rotation — dashboard-compatible
            jsonl_handler = TimedRotatingFileHandler(
                f"logs/{name}.jsonl",
                when="midnight",
                retention_days=30,
                compress=self.config.get("compression", False),
            )
            jsonl_handler.setFormatter(JSONLineFormatter(source=name))
            logger.add_handler(jsonl_handler)
        elif self.config.get("file_logging"):
            # Plain text with size-based rotation
            text_handler = FileHandler(
                f"logs/{name}.log",
                max_size=100 * 1024 * 1024,  # 100 MB
                backup_count=self.config.get("backup_count", 10),
                compress=self.config.get("compression", False),
            )
            logger.add_handler(text_handler)

        return logger


class SecurityLogger:
    """Specialized logger for security events."""

    def __init__(self, config: LoggingConfiguration = None):
        if config:
            self.logger = config.create_production_logger("security")
        else:
            self.logger = Logger("security")
        self.alert_threshold = 5  # Alert after 5 security events
        self.security_events = []

    @log
    def log_authentication_attempt(
        self, username: str, success: bool, ip_address: str, user_agent: str = None
    ):
        """Log authentication attempts with security context."""
        event = {
            "event_type": "authentication_attempt",
            "username": username,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.now().isoformat(),
        }

        if success:
            self.logger.info(
                f"Successful authentication for user {username} from {ip_address}", extra=event
            )
        else:
            self.logger.warning(
                f"Failed authentication attempt for user {username} from {ip_address}", extra=event
            )
            self._check_security_alerts(username, ip_address)

    @log
    def log_authorization_failure(self, username: str, resource: str, action: str, ip_address: str):
        """Log authorization failures."""
        event = {
            "event_type": "authorization_failure",
            "username": username,
            "resource": resource,
            "action": action,
            "ip_address": ip_address,
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.error(
            f"Authorization failed: User {username} attempted {action} on {resource}", extra=event
        )

        self._check_security_alerts(username, ip_address)

    @log
    def log_data_access(
        self, username: str, resource: str, operation: str, sensitive: bool = False
    ):
        """Log data access for audit purposes."""
        event = {
            "event_type": "data_access",
            "username": username,
            "resource": resource,
            "operation": operation,
            "sensitive": sensitive,
            "timestamp": datetime.now().isoformat(),
        }

        level = "WARNING" if sensitive else "INFO"
        message = f"Data access: {username} performed {operation} on {resource}"

        if sensitive:
            message += " (SENSITIVE DATA)"

        if level == "WARNING":
            self.logger.warning(message, extra=event)
        else:
            self.logger.info(message, extra=event)

    def _check_security_alerts(self, username: str, ip_address: str):
        """Check if security alerts should be triggered."""
        current_time = datetime.now()

        # Remove old events (older than 1 hour)
        self.security_events = [
            event
            for event in self.security_events
            if current_time - event["timestamp"] < timedelta(hours=1)
        ]

        # Add current event
        self.security_events.append(
            {"username": username, "ip_address": ip_address, "timestamp": current_time}
        )

        # Check for suspicious activity
        recent_failures = len(
            [
                event
                for event in self.security_events
                if event["ip_address"] == ip_address
                and current_time - event["timestamp"] < timedelta(minutes=15)
            ]
        )

        if recent_failures >= self.alert_threshold:
            self.logger.critical(
                f"SECURITY ALERT: {recent_failures} failed attempts from {ip_address} in 15 minutes",
                extra={
                    "alert_type": "suspicious_activity",
                    "ip_address": ip_address,
                    "failure_count": recent_failures,
                    "time_window": "15_minutes",
                },
            )


class PerformanceMonitor:
    """Monitor application performance with detailed logging."""

    def __init__(self, config: LoggingConfiguration = None):
        if config:
            self.logger = config.create_production_logger("performance")
        else:
            self.logger = Logger("performance")
        self.metrics = {}
        self.alert_thresholds = {
            "response_time": 2.0,  # seconds
            "memory_usage": 80,  # percentage
            "cpu_usage": 85,  # percentage
            "error_rate": 5,  # percentage
        }

    @log
    def log_request_performance(
        self, endpoint: str, method: str, duration: float, status_code: int, user_id: str = None
    ):
        """Log request performance metrics."""
        metric_key = f"{method}_{endpoint}"

        if metric_key not in self.metrics:
            self.metrics[metric_key] = {
                "requests": 0,
                "total_duration": 0,
                "errors": 0,
                "last_updated": datetime.now(),
            }

        # Update metrics
        self.metrics[metric_key]["requests"] += 1
        self.metrics[metric_key]["total_duration"] += duration
        if status_code >= 400:
            self.metrics[metric_key]["errors"] += 1
        self.metrics[metric_key]["last_updated"] = datetime.now()

        # Calculate current error rate
        error_rate = (
            self.metrics[metric_key]["errors"] / self.metrics[metric_key]["requests"]
        ) * 100
        avg_duration = (
            self.metrics[metric_key]["total_duration"] / self.metrics[metric_key]["requests"]
        )

        event = {
            "event_type": "request_performance",
            "endpoint": endpoint,
            "method": method,
            "duration": duration,
            "status_code": status_code,
            "user_id": user_id,
            "avg_duration": avg_duration,
            "error_rate": error_rate,
        }

        # Log with appropriate level
        if duration > self.alert_thresholds["response_time"]:
            self.logger.warning(
                f"Slow request: {method} {endpoint} took {duration:.3f}s (threshold: {self.alert_thresholds['response_time']}s)",
                extra=event,
            )
        elif status_code >= 500:
            self.logger.error(
                f"Server error: {method} {endpoint} returned {status_code}", extra=event
            )
        else:
            self.logger.info(
                f"Request: {method} {endpoint} - {duration:.3f}s - {status_code}", extra=event
            )

        # Check for performance alerts
        if error_rate > self.alert_thresholds["error_rate"]:
            self.logger.critical(
                f"PERFORMANCE ALERT: High error rate {error_rate:.1f}% for {method} {endpoint}",
                extra={
                    "alert_type": "high_error_rate",
                    "endpoint": endpoint,
                    "error_rate": error_rate,
                    "threshold": self.alert_thresholds["error_rate"],
                },
            )

    @log
    def log_system_metrics(self, cpu_usage: float, memory_usage: float, disk_usage: float):
        """Log system performance metrics."""
        event = {
            "event_type": "system_metrics",
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "timestamp": datetime.now().isoformat(),
        }

        # Check thresholds
        alerts = []
        if cpu_usage > self.alert_thresholds["cpu_usage"]:
            alerts.append(f"CPU: {cpu_usage:.1f}%")
        if memory_usage > self.alert_thresholds["memory_usage"]:
            alerts.append(f"Memory: {memory_usage:.1f}%")

        if alerts:
            self.logger.critical(
                f"SYSTEM ALERT: High resource usage - {', '.join(alerts)}",
                extra={**event, "alert_type": "high_resource_usage"},
            )
        else:
            self.logger.debug(
                f"System metrics: CPU {cpu_usage:.1f}%, Memory {memory_usage:.1f}%, Disk {disk_usage:.1f}%",
                extra=event,
            )


class AuditLogger:
    """Compliance and audit logging."""

    def __init__(self, config: LoggingConfiguration = None):
        if config:
            self.logger = config.create_production_logger("audit")
        else:
            self.logger = Logger("audit")

    @log
    def log_data_modification(
        self,
        user_id: str,
        table: str,
        record_id: str,
        operation: str,
        old_values: dict = None,
        new_values: dict = None,
    ):
        """Log data modifications for audit trail."""
        event = {
            "event_type": "data_modification",
            "user_id": user_id,
            "table": table,
            "record_id": record_id,
            "operation": operation,
            "old_values": old_values,
            "new_values": new_values,
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.info(
            f"Data {operation}: User {user_id} modified {table} record {record_id}", extra=event
        )

    @log
    def log_configuration_change(
        self, user_id: str, component: str, setting: str, old_value: Any, new_value: Any
    ):
        """Log configuration changes."""
        event = {
            "event_type": "configuration_change",
            "user_id": user_id,
            "component": component,
            "setting": setting,
            "old_value": str(old_value),
            "new_value": str(new_value),
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.warning(
            f"Configuration changed: {component}.{setting} changed from '{old_value}' to '{new_value}' by user {user_id}",
            extra=event,
        )

    @log
    def log_compliance_event(
        self, event_type: str, details: dict, compliance_framework: str = "GDPR"
    ):
        """Log compliance-related events."""
        event = {
            "event_type": "compliance_event",
            "compliance_framework": compliance_framework,
            "compliance_event_type": event_type,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.info(f"Compliance event ({compliance_framework}): {event_type}", extra=event)


class LogAggregator:
    """Aggregate and analyze logs from multiple sources."""

    def __init__(self):
        self.logger = Logger("log_aggregator")
        self.aggregated_data = {}

    def start_aggregation(self):
        """Start log aggregation process."""
        self.logger.info("Starting log aggregation service")

        # Simulate aggregation in a separate thread
        def aggregate_logs():
            while True:
                try:
                    self._process_log_batch()
                    time.sleep(30)  # Process every 30 seconds
                except Exception as e:
                    self.logger.error(f"Log aggregation error: {e}")
                    time.sleep(60)  # Wait longer on error

        aggregation_thread = threading.Thread(target=aggregate_logs, daemon=True)
        aggregation_thread.start()

        self.logger.info("Log aggregation service started")

    def _process_log_batch(self):
        """Process a batch of logs for aggregation."""
        # Simulate processing logs from different sources
        sources = ["api", "database", "cache", "queue"]

        for source in sources:
            # Simulate log metrics
            error_count = random.randint(0, 10)
            warning_count = random.randint(5, 50)
            info_count = random.randint(100, 1000)

            self.aggregated_data[source] = {
                "errors": error_count,
                "warnings": warning_count,
                "info": info_count,
                "total": error_count + warning_count + info_count,
                "last_updated": datetime.now(),
            }

        # Log aggregated metrics
        total_errors = sum(data["errors"] for data in self.aggregated_data.values())
        total_logs = sum(data["total"] for data in self.aggregated_data.values())

        self.logger.info(
            f"Log aggregation summary: {total_logs} total logs, {total_errors} errors across {len(sources)} sources",
            extra={
                "total_logs": total_logs,
                "total_errors": total_errors,
                "sources": len(sources),
                "aggregation_timestamp": datetime.now().isoformat(),
            },
        )


async def simulate_production_application():
    """Simulate a production application with comprehensive logging."""
    print("=== Production-Ready Logging Architecture ===\n")

    # Initialize logging configuration
    env = Environment.PRODUCTION  # Change to test different environments
    config = LoggingConfiguration(env)
    config.apply_configuration()

    # Initialize specialized loggers with rotation handlers
    security_logger = SecurityLogger(config)
    performance_monitor = PerformanceMonitor(config)
    audit_logger = AuditLogger(config)
    log_aggregator = LogAggregator()

    # Start log aggregation
    log_aggregator.start_aggregation()

    print("1. Security Logging")
    print("-" * 20)

    # Simulate security events
    # Successful authentication
    security_logger.log_authentication_attempt("alice", True, "192.168.1.100", "Mozilla/5.0")
    security_logger.log_data_access("alice", "user_profiles", "read", sensitive=False)

    # Failed authentication attempts (potential attack)
    for i in range(6):
        security_logger.log_authentication_attempt("admin", False, "10.0.0.50", "curl/7.68.0")
        await asyncio.sleep(0.1)

    # Authorization failure
    security_logger.log_authorization_failure("bob", "/admin/users", "delete", "192.168.1.101")

    # Sensitive data access
    security_logger.log_data_access("alice", "payment_info", "read", sensitive=True)

    print("\n2. Performance Monitoring")
    print("-" * 30)

    # Simulate API requests with performance monitoring
    endpoints = [
        ("/api/users", "GET"),
        ("/api/users", "POST"),
        ("/api/orders", "GET"),
        ("/api/payments", "POST"),
    ]

    for _ in range(20):
        endpoint, method = random.choice(endpoints)
        duration = random.uniform(0.1, 3.0)  # Some will exceed threshold
        status_code = random.choices([200, 201, 400, 404, 500], weights=[70, 10, 10, 5, 5])[0]
        user_id = f"user_{random.randint(1, 100)}"

        performance_monitor.log_request_performance(
            endpoint, method, duration, status_code, user_id
        )
        await asyncio.sleep(0.05)

    # Log system metrics
    performance_monitor.log_system_metrics(
        cpu_usage=random.uniform(60, 95),  # Some will exceed threshold
        memory_usage=random.uniform(70, 90),
        disk_usage=random.uniform(40, 80),
    )

    print("\n3. Audit Logging")
    print("-" * 20)

    # Simulate audit events
    audit_logger.log_data_modification(
        user_id="alice",
        table="users",
        record_id="123",
        operation="update",
        old_values={"email": "alice@old.com", "name": "Alice"},
        new_values={"email": "alice@new.com", "name": "Alice Smith"},
    )

    audit_logger.log_configuration_change(
        user_id="admin",
        component="database",
        setting="connection_pool_size",
        old_value=10,
        new_value=20,
    )

    audit_logger.log_compliance_event(
        event_type="data_export",
        details={"user_id": "alice", "data_type": "personal_info", "destination": "user_request"},
        compliance_framework="GDPR",
    )

    print("\n4. Application Business Logic")
    print("-" * 35)

    # Simulate business operations with integrated logging
    app_logger = AsyncLogger("business_logic")

    @log
    async def process_order(order_id: str, user_id: str, amount: float):
        """Process an order with comprehensive logging."""
        start_time = time.time()

        try:
            await app_logger.info(
                f"Processing order {order_id} for user {user_id}, amount: ${amount}"
            )

            # Validate order
            if amount <= 0:
                raise ValueError("Invalid order amount")

            # Simulate payment processing
            await asyncio.sleep(0.1)

            # Log to audit trail
            audit_logger.log_data_modification(
                user_id=user_id,
                table="orders",
                record_id=order_id,
                operation="create",
                new_values={"amount": amount, "status": "completed"},
            )

            duration = time.time() - start_time
            performance_monitor.log_request_performance(
                "/api/orders", "POST", duration, 201, user_id
            )

            await app_logger.info(f"Order {order_id} processed successfully in {duration:.3f}s")
            return True

        except Exception as e:
            duration = time.time() - start_time
            await app_logger.error(f"Order {order_id} processing failed: {e}")

            performance_monitor.log_request_performance(
                "/api/orders", "POST", duration, 500, user_id
            )

            raise

    # Process several orders
    orders = [
        ("order_001", "user_123", 99.99),
        ("order_002", "user_456", 149.50),
        ("order_003", "user_789", -10.00),  # Invalid amount
        ("order_004", "user_123", 299.99),
    ]

    for order_id, user_id, amount in orders:
        try:
            await process_order(order_id, user_id, amount)
        except ValueError:
            pass  # Expected for invalid order
        await asyncio.sleep(0.1)

    print("\n5. Log Analysis and Alerting")
    print("-" * 35)

    # Simulate log analysis
    analysis_logger = Logger("log_analysis")

    # Analyze recent logs (simulated)
    analysis_logger.info("Starting automated log analysis")

    # Report on security incidents
    analysis_logger.warning(
        "Security analysis: 6 failed login attempts detected from suspicious IP"
    )

    # Report on performance issues
    analysis_logger.warning(
        "Performance analysis: 3 slow requests detected, average response time increased by 25%"
    )

    # Report on system health
    analysis_logger.info("System health: All services operational, no critical alerts")

    await asyncio.sleep(2)  # Let aggregation run

    print("\n✓ Production logging architecture demonstration complete!")


import random


def main():
    """Main function."""
    print("=== Production-Ready Logging Architecture Demo ===\n")

    # Run the production simulation
    asyncio.run(simulate_production_application())

    print("\nProduction Logging Features Demonstrated:")
    print("- Multi-environment configuration management")
    print("- File rotation (daily JSONL + size-based text) via create_production_logger()")
    print("- JSONLineFormatter for dashboard-compatible structured output")
    print("- Security event logging and alerting")
    print("- Performance monitoring with thresholds")
    print("- Audit trail for compliance")
    print("- Log aggregation and analysis")
    print("- Structured logging with metadata")
    print("- Alert integration for critical events")
    print("- Business logic integration")


if __name__ == "__main__":
    main()
