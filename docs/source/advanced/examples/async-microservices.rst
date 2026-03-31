Async Microservices Architecture
================================

This example demonstrates intelligent type casting in a realistic e-commerce order processing system with multiple microservices, mixed async/sync operations, error handling, and concurrent processing.

Overview
--------

**Architecture**: Multi-service e-commerce order processing system

**Key Components**:
- **Database Service**: Connection pooling, data validation, async/sync operations
- **Payment Service**: External API integration, retry logic, transaction processing
- **Shipping Service**: Concurrent carrier queries, geographic calculations
- **Order Processing**: Main orchestration service combining all components

**Intelligent Type Casting Features**:
- Same ``@log`` decorator works with both async and sync methods
- Automatic sync wrapper creation for sync methods in async contexts
- Seamless logger integration across all services
- No manual logger management required

**File Location**: ``examples/04_async_services/production_grade_example.py``

Architecture Diagram
---------------------

.. code-block:: text

   ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
   │   Order Service     │    │  Payment Service    │    │  Shipping Service   │
   │  (Orchestration)    │    │  (External APIs)    │    │ (Concurrent APIs)   │
   │                     │    │                     │    │                     │
   │ • Async workflows   │────│ • Retry logic       │    │ • Multi-carrier     │
   │ • Sync validation   │    │ • Sync validation   │    │ • Sync calculations │
   │ • Error handling    │    │ • Async API calls   │    │ • Async API calls   │
   └─────────┬───────────┘    └─────────────────────┘    └─────────────────────┘
             │
             ▼
   ┌─────────────────────┐
   │  Database Service   │
   │ (Resource Pooling)  │
   │                     │
   │ • Connection pool   │
   │ • Async operations  │
   │ • Sync validations  │
   │ • Resource cleanup  │
   └─────────────────────┘

Complete Implementation
-----------------------

**Imports and Data Models**

.. code-block:: python

   #!/usr/bin/env python3
   """
   Production-Grade Async Services Example
   =======================================

   This example demonstrates LogEverything's intelligent type casting in a realistic
   production environment with:
   - Complex business logic
   - Mixed async/sync operations
   - Error handling and retries
   - Database operations
   - External API calls
   - Background tasks
   - Complex data flows

   Key Production Features:
   - Proper error handling with logging
   - Retry mechanisms with exponential backoff
   - Database connection pooling simulation
   - External service integrations
   - Complex business workflows
   - Performance monitoring
   - Resource cleanup
   """

   import asyncio
   import json
   import random
   import time
   from dataclasses import dataclass, asdict
   from datetime import datetime, timedelta
   from typing import Dict, List, Optional, Any
   from enum import Enum

   from logeverything.asyncio import AsyncLogger
   from logeverything.decorators import log
   from logeverything.core import register_logger


   class OrderStatus(Enum):
       PENDING = "pending"
       PROCESSING = "processing"
       SHIPPED = "shipped"
       DELIVERED = "delivered"
       CANCELLED = "cancelled"


   @dataclass
   class Order:
       id: str
       customer_id: str
       items: List[Dict[str, Any]]
       total_amount: float
       status: OrderStatus
       created_at: datetime
       shipping_address: Dict[str, str]


   @dataclass
   class PaymentResult:
       success: bool
       transaction_id: Optional[str]
       error_message: Optional[str]
       processing_fee: float

**Database Service with Connection Pooling**

.. code-block:: python

   class DatabaseService:
       """Simulates a complex database service with connection pooling."""

       def __init__(self):
           self.log = AsyncLogger("database", level="INFO")
           register_logger("database", self.log)
           self._connection_pool_size = 5
           self._active_connections = 0

       @log(using="database")
       async def get_connection(self) -> Dict[str, Any]:
           """Simulate getting a database connection from pool."""
           if self._active_connections >= self._connection_pool_size:
               self.log.warning("⚠️ Connection pool exhausted, waiting...")
               await asyncio.sleep(0.1)

           self._active_connections += 1
           conn_id = f"conn_{random.randint(1000, 9999)}"
           self.log.info(f"🔗 Acquired database connection {conn_id}")
           return {"id": conn_id, "created_at": time.time()}

       @log(using="database")
       def release_connection(self, connection: Dict[str, Any]) -> None:
           """Sync method - demonstrates type casting!"""
           self._active_connections = max(0, self._active_connections - 1)
           self.log.info(f"🔓 Released database connection {connection['id']}")

       @log(using="database")
       async def save_order(self, order: Order) -> bool:
           """Complex database save operation."""
           conn = await self.get_connection()
           try:
               # Simulate complex database operations
               self.log.info(f"💾 Saving order {order.id} to database")

               # Validate data integrity (sync operation within async)
               self._validate_order_data(order)

               # Simulate async database write
               await asyncio.sleep(0.05)  # Database latency

               # Update indexes (another sync operation)
               self._update_search_indexes(order)

               self.log.info(f"✅ Order {order.id} saved successfully")
               return True

           except Exception as e:
               self.log.error(f"❌ Failed to save order {order.id}: {str(e)}")
               return False
           finally:
               self.release_connection(conn)  # Sync method called from async context

       @log(using="database")
       def _validate_order_data(self, order: Order) -> None:
           """Sync validation method - type casting handles this seamlessly."""
           if not order.customer_id:
               raise ValueError("Customer ID is required")
           if order.total_amount <= 0:
               raise ValueError("Order amount must be positive")
           if not order.items:
               raise ValueError("Order must contain items")
           self.log.info(f"✅ Order {order.id} data validation passed")

       @log(using="database")
       def _update_search_indexes(self, order: Order) -> None:
           """Sync indexing operation."""
           # Simulate index updates
           self.log.info(f"🔍 Updated search indexes for order {order.id}")

**Type Casting in Action**: Notice how ``release_connection()`` and ``_validate_order_data()`` are sync methods called from async contexts. The intelligent type casting automatically creates ``database_sync_temp`` wrappers for these operations.

**Payment Service with Retry Logic**

.. code-block:: python

   class PaymentService:
       """External payment service integration."""

       def __init__(self):
           self.log = AsyncLogger("payment", level="INFO")
           register_logger("payment", self.log)
           self._api_key = "prod_key_12345"

       @log(using="payment")
       async def process_payment_with_retry(self, order: Order, max_retries: int = 3) -> PaymentResult:
           """Complex payment processing with retry logic."""
           for attempt in range(1, max_retries + 1):
               try:
                   self.log.info(f"💳 Processing payment for order {order.id} (attempt {attempt}/{max_retries})")

                   # Validate payment data (sync)
                   self._validate_payment_data(order)

                   # Make API call (async)
                   result = await self._make_payment_api_call(order)

                   if result.success:
                       # Log transaction (sync)
                       self._log_successful_transaction(result)
                       return result
                   else:
                       self.log.warning(f"⚠️ Payment failed: {result.error_message}")

               except Exception as e:
                   self.log.error(f"❌ Payment attempt {attempt} failed: {str(e)}")

                   if attempt < max_retries:
                       # Exponential backoff
                       wait_time = 2 ** attempt
                       self.log.info(f"⏰ Retrying in {wait_time}s...")
                       await asyncio.sleep(wait_time)
                   else:
                       return PaymentResult(
                           success=False,
                           transaction_id=None,
                           error_message=f"Payment failed after {max_retries} attempts",
                           processing_fee=0.0
                       )

       @log(using="payment")
       def _validate_payment_data(self, order: Order) -> None:
           """Sync validation - type casting in action."""
           if order.total_amount > 10000:
               raise ValueError("Amount exceeds daily limit")
           self.log.info(f"✅ Payment validation passed for order {order.id}")

       @log(using="payment")
       async def _make_payment_api_call(self, order: Order) -> PaymentResult:
           """Simulate external payment API call."""
           # Simulate API latency
           await asyncio.sleep(0.2)

           # Simulate occasional failures (20% failure rate)
           if random.random() < 0.2:
               return PaymentResult(
                   success=False,
                   transaction_id=None,
                   error_message="Insufficient funds",
                   processing_fee=0.0
               )

           # Successful payment
           transaction_id = f"txn_{random.randint(100000, 999999)}"
           fee = order.total_amount * 0.029  # 2.9% processing fee

           return PaymentResult(
               success=True,
               transaction_id=transaction_id,
               error_message=None,
               processing_fee=fee
           )

       @log(using="payment")
       def _log_successful_transaction(self, result: PaymentResult) -> None:
           """Sync transaction logging."""
           self.log.info(f"💰 Transaction {result.transaction_id} completed (fee: ${result.processing_fee:.2f})")

**Retry Pattern**: This service demonstrates complex retry logic with exponential backoff, where sync validation and logging methods are seamlessly integrated into the async retry flow.

**Shipping Service with Concurrent Operations**

.. code-block:: python

   class ShippingService:
       """Complex shipping and logistics service."""

       def __init__(self):
           self.log = AsyncLogger("shipping", level="INFO")
           register_logger("shipping", self.log)

       @log(using="shipping")
       async def calculate_shipping_options(self, order: Order) -> List[Dict[str, Any]]:
           """Complex shipping calculation with multiple carriers."""
           self.log.info(f"📦 Calculating shipping options for order {order.id}")

           # Get shipping zones (sync calculation)
           zone = self._determine_shipping_zone(order.shipping_address)

           # Calculate weight (sync)
           total_weight = self._calculate_package_weight(order.items)

           # Query multiple carriers concurrently (async)
           carrier_tasks = [
               self._query_carrier("FedEx", zone, total_weight),
               self._query_carrier("UPS", zone, total_weight),
               self._query_carrier("USPS", zone, total_weight)
           ]

           carrier_options = await asyncio.gather(*carrier_tasks, return_exceptions=True)

           # Filter successful responses and sort by price (sync processing)
           valid_options = self._process_carrier_responses(carrier_options)

           self.log.info(f"✅ Found {len(valid_options)} shipping options for order {order.id}")
           return valid_options

       @log(using="shipping")
       def _determine_shipping_zone(self, address: Dict[str, str]) -> str:
           """Sync geographic calculation - type casting handles this."""
           # Simplified zone logic
           state = address.get("state", "").upper()
           if state in ["CA", "OR", "WA"]:
               zone = "West"
           elif state in ["NY", "NJ", "CT", "MA"]:
               zone = "Northeast"
           else:
               zone = "Central"

           self.log.info(f"📍 Determined shipping zone: {zone}")
           return zone

       @log(using="shipping")
       def _calculate_package_weight(self, items: List[Dict[str, Any]]) -> float:
           """Sync weight calculation."""
           total_weight = sum(item.get("weight", 1.0) * item.get("quantity", 1) for item in items)
           self.log.info(f"⚖️ Total package weight: {total_weight} lbs")
           return total_weight

       @log(using="shipping")
       async def _query_carrier(self, carrier: str, zone: str, weight: float) -> Dict[str, Any]:
           """Async carrier API query."""
           # Simulate API call latency
           await asyncio.sleep(random.uniform(0.1, 0.3))

           # Simulate occasional API failures
           if random.random() < 0.1:
               raise Exception(f"{carrier} API temporarily unavailable")

           # Calculate shipping cost (simplified)
           base_cost = {"West": 8.99, "Northeast": 12.99, "Central": 10.99}[zone]
           weight_cost = weight * 1.5
           total_cost = base_cost + weight_cost

           return {
               "carrier": carrier,
               "cost": round(total_cost, 2),
               "delivery_days": random.randint(2, 7),
               "tracking_available": True
           }

       @log(using="shipping")
       def _process_carrier_responses(self, responses: List[Any]) -> List[Dict[str, Any]]:
           """Sync response processing."""
           valid_options = []
           for response in responses:
               if isinstance(response, dict):  # Successful response
                   valid_options.append(response)
               else:  # Exception
                   self.log.warning(f"⚠️ Carrier query failed: {str(response)}")

           # Sort by cost
           valid_options.sort(key=lambda x: x["cost"])
           return valid_options

**Concurrent Pattern**: This service demonstrates how sync calculations (zone determination, weight calculation) and async API calls can be mixed seamlessly with intelligent type casting.

**Order Processing Service - Main Orchestration**

.. code-block:: python

   class OrderProcessingService:
       """Main orchestration service combining all components."""

       def __init__(self):
           self.log = AsyncLogger("order_processor", level="INFO")
           register_logger("order_processor", self.log)

           # Inject dependencies
           self.db = DatabaseService()
           self.payment = PaymentService()
           self.shipping = ShippingService()

       @log(using="order_processor")
       async def process_order_workflow(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
           """Complete order processing workflow - production complexity."""
           workflow_id = f"workflow_{random.randint(10000, 99999)}"

           async with self.log.context(f"OrderWorkflow-{workflow_id}"):
               self.log.info(f"🚀 Starting order processing workflow {workflow_id}")

               try:
                   # Step 1: Create order object (sync processing)
                   order = self._create_order_from_data(order_data)

                   # Step 2: Save to database (async with sync sub-operations)
                   save_success = await self.db.save_order(order)
                   if not save_success:
                       raise Exception("Failed to save order to database")

                   # Step 3: Process payment with retries (complex async flow)
                   payment_result = await self.payment.process_payment_with_retry(order)
                   if not payment_result.success:
                       await self._handle_payment_failure(order, payment_result.error_message)
                       return {"status": "failed", "reason": "payment_failed"}

                   # Step 4: Calculate shipping options (mixed async/sync operations)
                   shipping_options = await self.shipping.calculate_shipping_options(order)
                   if not shipping_options:
                       self.log.warning("⚠️ No shipping options available")

                   # Step 5: Update order status (sync operation)
                   self._update_order_status(order, OrderStatus.PROCESSING)

                   # Step 6: Final database update (async)
                   await self.db.save_order(order)

                   # Step 7: Generate workflow result (sync processing)
                   result = self._generate_workflow_result(order, payment_result, shipping_options)

                   self.log.info(f"✅ Order workflow {workflow_id} completed successfully")
                   return result

               except Exception as e:
                   self.log.error(f"❌ Order workflow {workflow_id} failed: {str(e)}")
                   return {"status": "failed", "reason": str(e)}

       @log(using="order_processor")
       def _create_order_from_data(self, order_data: Dict[str, Any]) -> Order:
           """Sync order creation - type casting handles seamlessly."""
           order = Order(
               id=f"ord_{random.randint(100000, 999999)}",
               customer_id=order_data["customer_id"],
               items=order_data["items"],
               total_amount=sum(item["price"] * item["quantity"] for item in order_data["items"]),
               status=OrderStatus.PENDING,
               created_at=datetime.now(),
               shipping_address=order_data["shipping_address"]
           )
           self.log.info(f"📝 Created order {order.id} for customer {order.customer_id}")
           return order

       @log(using="order_processor")
       async def _handle_payment_failure(self, order: Order, error_message: str) -> None:
           """Async error handling."""
           self.log.error(f"💳 Payment failed for order {order.id}: {error_message}")
           order.status = OrderStatus.CANCELLED
           await self.db.save_order(order)

       @log(using="order_processor")
       def _update_order_status(self, order: Order, new_status: OrderStatus) -> None:
           """Sync status update."""
           old_status = order.status
           order.status = new_status
           self.log.info(f"📊 Order {order.id} status: {old_status.value} → {new_status.value}")

       @log(using="order_processor")
       def _generate_workflow_result(self, order: Order, payment: PaymentResult, shipping: List[Dict]) -> Dict[str, Any]:
           """Sync result generation."""
           return {
               "status": "success",
               "order_id": order.id,
               "transaction_id": payment.transaction_id,
               "processing_fee": payment.processing_fee,
               "shipping_options": len(shipping),
               "estimated_delivery": "3-5 business days",
               "total_cost": order.total_amount + payment.processing_fee
           }

       @log(using="order_processor")
       async def process_multiple_orders_concurrently(self, orders_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
           """Production-grade batch processing."""
           batch_id = f"batch_{random.randint(10000, 99999)}"

           async with self.log.context(f"BatchProcess-{batch_id}"):
               self.log.info(f"🔄 Processing batch {batch_id} with {len(orders_batch)} orders")

               # Process all orders concurrently
               tasks = [self.process_order_workflow(order_data) for order_data in orders_batch]
               results = await asyncio.gather(*tasks, return_exceptions=True)

               # Analyze results (sync processing)
               success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "success")
               failure_count = len(results) - success_count

               self.log.info(f"📊 Batch {batch_id} completed: {success_count} success, {failure_count} failures")
               return [r if isinstance(r, dict) else {"status": "error", "reason": str(r)} for r in results]

**Demo Implementation**

.. code-block:: python

   async def demo_production_complexity():
       """Demonstrate production-grade complexity with intelligent type casting."""
       print("🏭 Production-Grade Async Services Demo")
       print("=" * 50)
       print("This demonstrates LogEverything's intelligent type casting in a realistic")
       print("production environment with complex business logic, error handling,")
       print("database operations, external APIs, and mixed async/sync workflows.")
       print()

       # Create the main service
       processor = OrderProcessingService()

       # Sample order data
       sample_orders = [
           {
               "customer_id": "cust_123",
               "items": [
                   {"name": "Laptop", "price": 999.99, "quantity": 1, "weight": 4.5},
                   {"name": "Mouse", "price": 29.99, "quantity": 2, "weight": 0.3}
               ],
               "shipping_address": {
                   "street": "123 Main St",
                   "city": "San Francisco",
                   "state": "CA",
                   "zip": "94105"
               }
           },
           {
               "customer_id": "cust_456",
               "items": [
                   {"name": "Phone", "price": 799.99, "quantity": 1, "weight": 0.5},
                   {"name": "Case", "price": 39.99, "quantity": 1, "weight": 0.2}
               ],
               "shipping_address": {
                   "street": "456 Oak Ave",
                   "city": "New York",
                   "state": "NY",
                   "zip": "10001"
               }
           }
       ]

       print("📝 Processing Single Complex Order:")
       print("-" * 40)
       single_result = await processor.process_order_workflow(sample_orders[0])

       print("\n📝 Processing Multiple Orders Concurrently:")
       print("-" * 45)
       batch_results = await processor.process_multiple_orders_concurrently(sample_orders)

       print("\n📊 Final Results:")
       print("-" * 20)
       print(f"Single order result: {json.dumps(single_result, indent=2)}")
       print(f"\nBatch processing: {len(batch_results)} orders completed")

       print("\n🎯 Production Features Demonstrated:")
       print("• Complex business workflows with multiple services")
       print("• Mixed async/sync operations with intelligent type casting")
       print("• Error handling and retry mechanisms")
       print("• Database operations with connection pooling")
       print("• External API integrations")
       print("• Concurrent processing and resource management")
       print("• Comprehensive logging throughout the entire stack")


   if __name__ == "__main__":
       asyncio.run(demo_production_complexity())

Running the Example
-------------------

.. code-block:: bash

   cd logeverything
   python examples/04_async_services/production_grade_example.py

Sample Output Analysis
----------------------

The example produces structured logging output that clearly shows intelligent type casting in action:

.. code-block:: text

   🏭 Production-Grade Async Services Demo
   AsyncLogger: Auto-detected environment: script

   📝 Processing Single Complex Order:
   2025-06-30 22:42:32 | INFO | order_processor:459 | 🔵 CALL OrderProcessingService.process_order_workflow(...)
   2025-06-30 22:42:32 | INFO | order_processor:238 | [context=OrderWorkflow-workflow_41248] 🚀 Starting order processing workflow
   2025-06-30 22:42:32 | INFO | database:459 | 🔵 CALL DatabaseService.save_order(...)
   2025-06-30 22:42:32 | INFO | database_sync_temp:346 | 🔵 CALL DatabaseService._validate_order_data(...)  # ← Type casting!
   2025-06-30 22:42:32 | INFO | payment:459 | 🔵 CALL PaymentService.process_payment_with_retry(...)
   2025-06-30 22:42:32 | INFO | payment_sync_temp:346 | 🔵 CALL PaymentService._validate_payment_data(...)  # ← Sync within async
   2025-06-30 22:42:33 | INFO | shipping:459 | 🔵 CALL ShippingService.calculate_shipping_options(...)
   2025-06-30 22:42:33 | INFO | order_processor:480 | ✅ DONE OrderProcessingService.process_order_workflow (734.85ms)

**Key Observations**:

1. **Async Methods**: Use the original logger names (``database:459``, ``payment:459``)
2. **Sync Methods**: Automatically get ``_sync_temp`` wrappers (``database_sync_temp:346``, ``payment_sync_temp:346``)
3. **Seamless Integration**: No manual configuration required for type casting
4. **Performance Tracking**: Built-in timing for all operations (734.85ms total)
5. **Context Preservation**: Hierarchical logging maintains call relationships

Type Casting Benefits Demonstrated
----------------------------------

**Universal Decorator Usage**
   Same ``@log(using="service")`` decorator works for both async and sync methods without any configuration changes.

**Automatic Sync Wrapper Creation**
   When sync methods are called in async contexts, temporary sync loggers (``*_sync_temp``) are created automatically.

**Zero Configuration Overhead**
   No manual logger management, type checking, or special handling required by developers.

**Performance Monitoring**
   Built-in timing and call tracking works seamlessly across all operation types.

**Error Handling Integration**
   Exception tracking and retry logging work consistently across async and sync boundaries.

**Scalability Design**
   Concurrent processing with proper context isolation maintains logging clarity.

Production Adaptation Guidelines
--------------------------------

When adapting this example for your production environment:

**Service Architecture**
   - Replace mock services with real database, payment, and shipping integrations
   - Implement proper authentication and authorization
   - Add service discovery and load balancing
   - Include circuit breakers and bulkheads for resilience

**Error Handling**
   - Implement comprehensive exception hierarchies
   - Add alerting based on error patterns
   - Include dead letter queues for failed operations
   - Add rollback and compensation logic

**Performance Optimization**
   - Monitor the timing metrics provided by the logging
   - Implement caching for frequently accessed data
   - Add connection pooling for external services
   - Optimize database queries and indexes

**Security Considerations**
   - Sanitize sensitive data in log messages
   - Implement proper secret management
   - Add audit trails for financial operations
   - Include rate limiting and DDOS protection

**Monitoring & Observability**
   - Set up dashboards based on the structured log output
   - Create alerts for error thresholds and performance degradation
   - Implement distributed tracing for cross-service operations
   - Add health checks and readiness probes

.. note::
   This example demonstrates the logging patterns and intelligent type casting
   behavior. The business logic is simplified for clarity - real production
   systems would include additional validation, security, and error handling
   appropriate for financial and shipping operations.

.. tip::
   Focus on the logging patterns rather than the specific business logic.
   The key takeaway is how the same ``@log`` decorator seamlessly handles
   mixed async/sync operations across multiple services without any manual
   logger management or type checking.
