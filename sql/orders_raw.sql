CREATE OR REPLACE TABLE `orbit-test-project-468319.ecommerce_orders.orders_raw`
(
  -- Schema Definition
  order_id STRING NOT NULL,
  order_date TIMESTAMP NOT NULL,
  order_details STRING,
  order_status STRING NOT NULL,
  ingestion_timestamp TIMESTAMP NOT NULL
)
-- Performance Optimization
PARTITION BY DATE(order_date);