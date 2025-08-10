-- Returns the first event for each order
WITH RankedEvents AS (
  SELECT
 order_id,
 order_date,
 -- Extract the hour for the Peak Order Hours chart
 EXTRACT(HOUR FROM order_date AT TIME ZONE 'America/New_York') AS order_hour,
  order_details,
  order_status,
    ROW_NUMBER() OVER(PARTITION BY order_id ORDER BY order_date ASC) as rn
  FROM
    `orbit-test-project-468319.ecommerce_orders.orders_raw`
)
SELECT *
FROM RankedEvents
WHERE rn = 1