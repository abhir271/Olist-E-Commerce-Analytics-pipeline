"""
STEP 1: Connect to your Olist PostgreSQL database and generate
business summary text chunks that we'll embed in Step 2.

Run this first. It just prints summaries to the screen and saves
them to summaries.json so you can sanity-check the numbers before
we embed anything.
"""

import psycopg2
import json
import os

# ---- EDIT THESE TO MATCH YOUR SETUP ----
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "ecommerce_pipeline",      #dbname
    "user": "postgres",
    "password": os.environ.get("DB_PASSWORD"),  # password
}
# -----------------------------------------

def run_query(cur, sql):
    cur.execute(sql)
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    return cols, rows

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # First, let's see what tables you actually have
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = [r[0] for r in cur.fetchall()]
    print("Tables found in your database:")
    for t in tables:
        print(f"  - {t}")
    print()

    if not tables:
        print("No tables found in 'public' schema. Check your DB_CONFIG dbname.")
        return

    print("Paste this table list back to me in chat, and I'll write the")
    print("exact SQL queries for your specific Olist schema in Step 1b.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()