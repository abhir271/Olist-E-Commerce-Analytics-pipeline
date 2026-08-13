-- Business Question 1: Which product categories generate the most revenue?

SELECT product_category_translation.product_category_name_english, SUM(price) AS total_revenue
FROM order_items
JOIN products ON order_items.product_id = products.product_id
JOIN product_category_translation ON products.product_category_name = product_category_translation.product_category_name
GROUP BY product_category_translation.product_category_name_english
ORDER BY total_revenue DESC;

-- Business Question 2: Does delivery time affect review scores?

SELECT review_score,
       AVG(EXTRACT(DAY FROM orders.order_delivered_customer_date - orders.order_purchase_timestamp)) AS avg_delivery_days
FROM orders
JOIN order_reviews ON orders.order_id = order_reviews.order_id
WHERE orders.order_delivered_customer_date IS NOT NULL
GROUP BY review_score
ORDER BY review_score DESC;

-- Business Question 3: What is the repeat purchase rate?

SELECT 
    COUNT(DISTINCT customer_unique_id) AS total_customers,
    COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) AS repeat_customers,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_unique_id END) / COUNT(DISTINCT customer_unique_id), 2) AS repeat_rate_pct
FROM (
    SELECT customers.customer_unique_id, COUNT(orders.order_id) AS order_count
    FROM customers
    JOIN orders ON customers.customer_id = orders.customer_id
    GROUP BY customers.customer_unique_id
) AS customer_orders;

-- Business Question 4: How does seller performance vary?

SELECT 
    order_items.seller_id,
    COUNT(DISTINCT order_items.order_id) AS total_orders,
    SUM(order_items.price) AS total_revenue,
    ROUND(AVG(order_reviews.review_score), 2) AS avg_review_score
FROM order_items
JOIN order_reviews ON order_items.order_id = order_reviews.order_id
GROUP BY order_items.seller_id
ORDER BY total_revenue DESC
LIMIT 20;