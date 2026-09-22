"""
STEP 1b: Runs real business-question SQL against your Olist tables
and turns each result into a plain-English summary "chunk" — these
chunks are what we'll embed in Step 2 for retrieval.

Edit DB_CONFIG below, then run:
    python s1b_generate_summaries.py

It will print each summary AND save them all to summaries.json.
Read through the printed output and sanity-check the numbers look
reasonable before moving to Step 2.
"""

import psycopg2
import json
import os

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "ecommerce_pipeline",       # dbname
    "user": "postgres",
    "password": os.environ.get("DB_PASSWORD"),  # password
}

def fetch(cur, sql, params=None):
    cur.execute(sql, params or ())
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    summaries = []

    # 1. Overall volume & revenue
    r = fetch(cur, """
        SELECT COUNT(DISTINCT o.order_id) AS total_orders,
               ROUND(SUM(oi.price + oi.freight_value)::numeric, 2) AS total_revenue
        FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered';
    """)[0]
    summaries.append(
        f"Overall business volume: {r['total_orders']} delivered orders generated "
        f"total revenue of R${r['total_revenue']} (including freight)."
    )

    # 2. Top 5 categories by revenue
    r = fetch(cur, """
        SELECT COALESCE(t.product_category_name_english, p.product_category_name) AS category,
               ROUND(SUM(oi.price)::numeric, 2) AS revenue,
               COUNT(*) AS items_sold
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        LEFT JOIN product_category_translation t ON p.product_category_name = t.product_category_name
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY category ORDER BY revenue DESC LIMIT 5;
    """)
    lines = "; ".join(f"{x['category']}: R${x['revenue']} ({x['items_sold']} items)" for x in r)
    summaries.append(f"Top 5 product categories by revenue: {lines}.")

    # 3. Delivery performance (on-time vs late)
    r = fetch(cur, """
        SELECT
          COUNT(*) FILTER (WHERE order_delivered_customer_date <= order_estimated_delivery_date) AS on_time,
          COUNT(*) FILTER (WHERE order_delivered_customer_date > order_estimated_delivery_date) AS late,
          COUNT(*) AS total
        FROM orders
        WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL;
    """)[0]
    pct_late = round(100 * r["late"] / r["total"], 1) if r["total"] else 0
    summaries.append(
        f"Delivery performance: out of {r['total']} delivered orders, {r['on_time']} arrived "
        f"on time and {r['late']} arrived late ({pct_late}% late delivery rate)."
    )

    # 4. Average delivery time (days)
    r = fetch(cur, """
        SELECT ROUND(AVG(EXTRACT(EPOCH FROM (order_delivered_customer_date - order_purchase_timestamp))/86400)::numeric, 1) AS avg_days
        FROM orders
        WHERE order_status = 'delivered' AND order_delivered_customer_date IS NOT NULL;
    """)[0]
    summaries.append(f"Average delivery time across all orders: {r['avg_days']} days from purchase to customer delivery.")

    # 5. Worst 5 states by late delivery rate (min 20 orders)
    r = fetch(cur, """
        SELECT c.customer_state AS state,
               COUNT(*) AS total,
               ROUND(100.0 * COUNT(*) FILTER (WHERE o.order_delivered_customer_date > o.order_estimated_delivery_date) / COUNT(*), 1) AS pct_late
        FROM orders o JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
        GROUP BY c.customer_state
        HAVING COUNT(*) >= 20
        ORDER BY pct_late DESC LIMIT 5;
    """)
    lines = "; ".join(f"{x['state']}: {x['pct_late']}% late ({x['total']} orders)" for x in r)
    summaries.append(f"States with the highest late-delivery rates: {lines}.")

    # 6. Average review score, overall
    r = fetch(cur, "SELECT ROUND(AVG(review_score)::numeric, 2) AS avg_score, COUNT(*) AS n FROM order_reviews;")[0]
    summaries.append(f"Average customer review score across {r['n']} reviews: {r['avg_score']} out of 5.")

    # 7. Review score: on-time vs late deliveries
    r = fetch(cur, """
        SELECT
          ROUND(AVG(rv.review_score) FILTER (WHERE o.order_delivered_customer_date <= o.order_estimated_delivery_date)::numeric, 2) AS on_time_score,
          ROUND(AVG(rv.review_score) FILTER (WHERE o.order_delivered_customer_date > o.order_estimated_delivery_date)::numeric, 2) AS late_score
        FROM orders o
        JOIN order_reviews rv ON o.order_id = rv.order_id
        WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL;
    """)[0]
    summaries.append(
        f"Review scores by delivery outcome: on-time deliveries average {r['on_time_score']}/5, "
        f"late deliveries average {r['late_score']}/5."
    )

    # 8. Payment type breakdown
    r = fetch(cur, """
        SELECT payment_type, COUNT(*) AS n, ROUND(SUM(payment_value)::numeric, 2) AS total_value
        FROM order_payments GROUP BY payment_type ORDER BY total_value DESC;
    """)
    lines = "; ".join(f"{x['payment_type']}: {x['n']} payments, R${x['total_value']}" for x in r)
    summaries.append(f"Payment method breakdown: {lines}.")

    # 9. Top 5 states by revenue
    r = fetch(cur, """
        SELECT c.customer_state AS state, ROUND(SUM(oi.price)::numeric, 2) AS revenue
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY c.customer_state ORDER BY revenue DESC LIMIT 5;
    """)
    lines = "; ".join(f"{x['state']}: R${x['revenue']}" for x in r)
    summaries.append(f"Top 5 states by revenue: {lines}.")

    # 10. Category with best and worst average review score (min 30 reviews)
    r = fetch(cur, """
        SELECT COALESCE(t.product_category_name_english, p.product_category_name) AS category,
               ROUND(AVG(rv.review_score)::numeric, 2) AS avg_score,
               COUNT(*) AS n
        FROM order_reviews rv
        JOIN orders o ON rv.order_id = o.order_id
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        LEFT JOIN product_category_translation t ON p.product_category_name = t.product_category_name
        GROUP BY category HAVING COUNT(*) >= 30
        ORDER BY avg_score DESC LIMIT 1;
    """)[0]
    summaries.append(f"Highest-rated product category: {r['category']} with an average review score of {r['avg_score']}/5 across {r['n']} reviews.")

    r = fetch(cur, """
        SELECT COALESCE(t.product_category_name_english, p.product_category_name) AS category,
               ROUND(AVG(rv.review_score)::numeric, 2) AS avg_score,
               COUNT(*) AS n
        FROM order_reviews rv
        JOIN orders o ON rv.order_id = o.order_id
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        LEFT JOIN product_category_translation t ON p.product_category_name = t.product_category_name
        GROUP BY category HAVING COUNT(*) >= 30
        ORDER BY avg_score ASC LIMIT 1;
    """)[0]
    summaries.append(f"Lowest-rated product category: {r['category']} with an average review score of {r['avg_score']}/5 across {r['n']} reviews.")

    # Print + save
    print(f"\nGenerated {len(summaries)} business summaries:\n")
    for i, s in enumerate(summaries, 1):
        print(f"{i}. {s}\n")

    with open("summaries.json", "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)
    print("Saved to summaries.json")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()