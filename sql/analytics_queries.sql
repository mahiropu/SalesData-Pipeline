SELECT
    category,
    COUNT(*) AS orders,
    SUM(quantity) AS units_sold,
    ROUND(SUM(revenue), 2) AS total_revenue
FROM fact_orders
GROUP BY category
ORDER BY total_revenue DESC;

SELECT
    country,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(AVG(revenue), 2) AS avg_order_value
FROM fact_orders
GROUP BY country
ORDER BY total_revenue DESC;

SELECT
    order_date,
    COUNT(*) AS orders,
    ROUND(SUM(revenue), 2) AS daily_revenue
FROM fact_orders
GROUP BY order_date
ORDER BY order_date;

SELECT
    sku,
    product_name,
    SUM(quantity) AS units_sold,
    ROUND(SUM(revenue), 2) AS total_revenue
FROM fact_orders
GROUP BY sku, product_name
ORDER BY units_sold DESC
LIMIT 5;

SELECT
    customer_id,
    COUNT(*) AS orders,
    ROUND(SUM(revenue), 2) AS lifetime_value
FROM fact_orders
GROUP BY customer_id
ORDER BY lifetime_value DESC
LIMIT 10;
