-- This query transforms the event stream into a single summary row per order
-- and calculates the duration between key lifecycle events.
SELECT
    order_id,

    -- Use conditional aggregation to get the timestamp for each key status
    MIN(CASE WHEN order_status = 'Processing' THEN order_date END) AS processing_timestamp,
    MIN(CASE WHEN order_status = 'Shipped' THEN order_date END) AS shipped_timestamp,
    MIN(CASE WHEN order_status = 'Delivered' THEN order_date END) AS delivered_timestamp,
    MIN(CASE WHEN order_status = 'Returned' THEN order_date END) AS returned_timestamp,

    -- Calculate the duration between the events in hours
    TIMESTAMP_DIFF(
        MIN(CASE WHEN order_status = 'Shipped' THEN order_date END),
        MIN(CASE WHEN order_status = 'Processing' THEN order_date END),
        HOUR
    ) AS processing_to_ship_hours,

    -- Calculate the duration between the events in days
    TIMESTAMP_DIFF(
        MIN(CASE WHEN order_status = 'Delivered' THEN order_date END),
        MIN(CASE WHEN order_status = 'Shipped' THEN order_date END),
        DAY
    ) AS shipping_to_delivery_days

FROM
    `orbit-test-project-468319.ecommerce_orders.orders_raw`
GROUP BY
    order_id