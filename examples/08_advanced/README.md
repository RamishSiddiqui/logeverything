# Advanced Examples

This directory contains advanced examples showcasing sophisticated LogEverything usage patterns for production environments and complex scenarios.

## Examples in this category:

### 1. **production_logging_architecture.py** ⭐
- **Complete production-ready logging system**
- Multi-environment configuration (dev, staging, production)
- Security logging with attack detection and alerting
- Performance monitoring with automatic thresholds
- Audit logging for compliance (GDPR, SOX, etc.)
- Log aggregation and centralized analysis
- Alert integration for critical events
- **Essential for enterprise and production deployments**

### 2. **optional_dependencies_example.py**
- Handling optional dependencies gracefully
- Feature detection and fallback mechanisms
- Integration with external libraries
- Dependency management best practices

### 3. **multi_level_visual_alignment.py** ✨ **NEW!**
- **Advanced visual alignment with deep nesting (4+ levels)**
- Complex real-world scenarios with intricate call stacks
- Performance timing and monitoring at each nesting level
- Mixed logging contexts and context switching
- Production-ready patterns for complex applications
- **Perfect for understanding visual alignment in enterprise scenarios**

## Key Concepts Covered:

### Production Architecture
- **Multi-environment configs**: Different settings for dev/staging/production
- **Centralized logging**: Aggregation from multiple sources
- **Security monitoring**: Authentication, authorization, and access logging
- **Performance tracking**: Request timing, system metrics, alerting
- **Compliance logging**: Audit trails for regulatory requirements

### Security Features
- **Authentication logging**: Success/failure tracking with alert thresholds
- **Authorization monitoring**: Access control violations
- **Data access auditing**: Sensitive data access tracking
- **Attack detection**: Automated suspicious activity alerts
- **Incident response**: Structured logging for security investigations

### Performance Monitoring
- **Request performance**: Response time tracking with thresholds
- **System metrics**: CPU, memory, disk usage monitoring
- **Error rate tracking**: Automatic alerting on high error rates
- **SLA monitoring**: Service level agreement compliance
- **Capacity planning**: Resource usage trends and forecasting

### Compliance & Audit
- **Data modification tracking**: Who changed what, when
- **Configuration changes**: System setting modifications
- **Access logging**: Who accessed what data
- **Regulatory compliance**: GDPR, HIPAA, SOX requirements
- **Audit trails**: Complete transaction history

### Log Management
- **Log rotation**: Automatic file rotation and archival
- **Compression**: Space-efficient log storage
- **Retention policies**: Automatic cleanup based on age/size
- **Aggregation**: Centralized collection from multiple sources
- **Analysis**: Automated log analysis and pattern detection

## Production Architecture Example:

```python
from logeverything import Logger, configure
from logeverything.handlers import FileHandler, ConsoleHandler

# Environment-specific configuration
class ProductionConfig:
    def __init__(self, environment="production"):
        self.environment = environment
        self.setup_logging()

    def setup_logging(self):
        if self.environment == "production":
            configure(
                level="WARNING",           # Only warnings+ in production
                console_logging=False,     # No console output
                file_logging=True,         # File logging only
                structured_logging=True,   # JSON format
                security_logging=True,     # Security events
                performance_monitoring=True # Performance tracking
            )
        elif self.environment == "development":
            configure(
                level="DEBUG",             # All logs in development
                console_logging=True,      # Console output
                visual_mode=True,          # Pretty formatting
                use_symbols=True           # Visual indicators
            )

# Specialized loggers for different concerns
security_logger = Logger("security")
performance_logger = Logger("performance")
audit_logger = Logger("audit")

# Security event logging
def log_authentication(username, success, ip_address):
    if success:
        security_logger.info(f"Login successful: {username} from {ip_address}")
    else:
        security_logger.warning(f"Login failed: {username} from {ip_address}")
        # Check for attack patterns
        check_brute_force_attempts(username, ip_address)

# Performance monitoring
def log_request_performance(endpoint, duration, status_code):
    if duration > 2.0:  # Alert on slow requests
        performance_logger.warning(
            f"Slow request: {endpoint} took {duration:.3f}s",
            extra={'endpoint': endpoint, 'duration': duration, 'status': status_code}
        )
    else:
        performance_logger.info(
            f"Request: {endpoint} - {duration:.3f}s - {status_code}",
            extra={'endpoint': endpoint, 'duration': duration, 'status': status_code}
        )

# Audit logging for compliance
def log_data_modification(user_id, table, record_id, old_values, new_values):
    audit_logger.info(
        f"Data modified: {table}#{record_id} by user {user_id}",
        extra={
            'user_id': user_id,
            'table': table,
            'record_id': record_id,
            'old_values': old_values,
            'new_values': new_values,
            'timestamp': datetime.now().isoformat()
        }
    )
```

## Security Monitoring Features:

### Attack Detection
- **Brute force protection**: Failed login attempt tracking
- **IP-based monitoring**: Suspicious activity from specific IPs
- **Rate limiting**: Request frequency monitoring
- **Pattern recognition**: Automated attack pattern detection

### Access Control
- **Authorization failures**: Attempted unauthorized access
- **Privilege escalation**: Attempts to gain higher privileges
- **Data access**: Tracking who accessed what data
- **Administrative actions**: High-privilege operations

### Incident Response
- **Structured alerts**: Machine-readable security events
- **Correlation**: Related event linking
- **Timeline reconstruction**: Complete incident timeline
- **Evidence preservation**: Tamper-proof audit logs

## Recommended Learning Path:

1. **Prerequisites**: Master basic and core features first
2. **Start with**: `production_logging_architecture.py` - See the complete system
3. **Specialize**: `optional_dependencies_example.py` - Handle complex dependencies
4. **Implement**: Apply patterns to your production environment

## Production Checklist:

### ✅ Configuration
- [ ] Environment-specific log levels
- [ ] Appropriate handlers for each environment
- [ ] Log rotation and retention policies
- [ ] Structured logging format (JSON)

### ✅ Security
- [ ] Authentication/authorization logging
- [ ] Security event monitoring
- [ ] Attack detection and alerting
- [ ] Sensitive data access tracking

### ✅ Performance
- [ ] Request performance monitoring
- [ ] System resource tracking
- [ ] Alert thresholds configuration
- [ ] SLA monitoring setup

### ✅ Compliance
- [ ] Audit trail implementation
- [ ] Data modification logging
- [ ] Regulatory requirement compliance
- [ ] Retention policy enforcement

### ✅ Operations
- [ ] Log aggregation setup
- [ ] Monitoring dashboard integration
- [ ] Alert routing configuration
- [ ] Backup and recovery procedures

## Integration Examples:

### ELK Stack (Elasticsearch, Logstash, Kibana)
```python
# JSON structured logging for Logstash
configure(format_type="json", include_metadata=True)
```

### Prometheus/Grafana
```python
# Metrics logging for Prometheus scraping
performance_logger.info("request_duration_seconds", extra={'value': duration, 'labels': {'endpoint': '/api/users'}})
```

### Slack/PagerDuty Alerts
```python
# Critical alerts for immediate notification
security_logger.critical("SECURITY ALERT: Brute force attack detected", extra={'alert_channel': 'security'})
```

## Next Steps:

After implementing advanced patterns:
- **Monitor and tune**: Adjust thresholds based on actual usage
- **Scale horizontally**: Implement distributed logging
- **Automate analysis**: ML-based log analysis
- **Integrate SIEM**: Security Information and Event Management
