-- Returns the latest event for each order
SELECT
 order_id,
 order_date,
 order_details,
 order_status
FROM (
 SELECT *,
 ROW_NUMBER() OVER(PARTITION BY order_id ORDER BY order_date DESC) as rn
 FROM
 `orbit-test-project-468319.ecommerce_orders.orders_raw`
)
WHERE
 rn = 1