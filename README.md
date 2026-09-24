# Olist E-Commerce Analytics Pipeline with GenAI Insights Assistant

An end-to-end data analytics project using the Olist Brazilian E-Commerce dataset from raw CSVs to a published interactive dashboard, extended with a Retrieval-Augmented Generation (RAG) assistant for natural-language business questions.

**Live app:**  (https://olist-e-commerce-analytics-pipeline-72aijejfwqy7xvoohtjjgp.streamlit.app/)

## Overview

This project builds a complete analytics pipeline: designing a normalized PostgreSQL schema, cleaning and loading ~120K real e-commerce orders, writing SQL to answer business questions, and visualizing insights in an interactive Tableau dashboard. On top of that, it adds a GenAI layer a RAG system that lets you ask business questions in plain English and get answers grounded in the actual data, instead of writing SQL yourself.

## Business Questions Answered

1. Which product categories drive the most revenue?
2. Does delivery time affect customer review scores?
3. What is the repeat purchase rate?
4. How does seller performance vary across revenue and ratings?

## Tech Stack

**Analytics pipeline:**
- PostgreSQL — relational schema design, data storage
- Python (pandas, SQLAlchemy) — data cleaning, transformation, and loading
- SQL — business question analysis (multi-table joins, aggregations, subqueries)
- Tableau Public — interactive dashboard

**GenAI / RAG layer:**
- Python — orchestration
- Chroma — local vector database for semantic retrieval
- sentence-transformers (`all-MiniLM-L6-v2`) — local embedding model
- Anthropic Claude API — grounded answer generation
- Streamlit — combined web app (dashboard + chat interface)

## Key Findings

- Health & beauty and watches/gifts are the top-revenue categories.
- Delivery time shows a clear relationship with review scores — orders with longer delivery windows correlate with lower ratings.
- The repeat purchase rate is notably low (~3%), consistent with typical marketplace buying behavior.
- Seller revenue and review quality vary independently — some high-revenue sellers have below-average ratings, highlighting where satisfaction may need attention.

## Data Quality Process

- Verified referential integrity across all foreign keys before loading (zero orphaned records).
- Identified and resolved 2 missing product category translations not present in the source data.
- Discovered and corrected two incorrect schema assumptions using real data:
  - `customer_unique_id` is not unique — customers can have multiple orders under the same identity.
  - `review_id` is not a standalone primary key — Olist reuses review IDs across grouped orders, requiring a composite key.

## GenAI Insights Assistant (RAG)

On top of the SQL/Tableau analytics layer, this project adds a Retrieval-Augmented Generation system:

1. Key business metrics are precomputed via SQL and converted into plain-English summary chunks.
2. Those summaries are embedded locally with `sentence-transformers` and stored in a Chroma vector database.
3. A user question is embedded and matched against the most semantically similar summary chunks.
4. The retrieved chunks are passed to the Claude API as context, which generates a grounded answer or honestly declines if the data doesn't support an answer, rather than guessing.

**Validation:** Tested against a manually curated set of business questions. Initial testing (retrieving the top-2 most similar chunks) missed some in-scope answers due to a retrieval recall gap; increasing retrieval depth to top-3 chunks resolved this. The system now correctly answers in scope questions and correctly declines out of scope ones instead of hallucinating.

## Dashboard

[View the interactive Tableau dashboard](https://public.tableau.com/app/profile/abhishek.ravikumar8688/viz/OlistE-CommerceAnalytics_17865833504340/OlistE-CommerceAnalyticsDashboard)

## Running the GenAI Assistant Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set required environment variables:
   ```bash
   setx ANTHROPIC_API_KEY "your-claude-api-key"     # Windows
   setx DB_PASSWORD "your-postgres-password"         # only needed to regenerate summaries.json
   ```

3. (Optional) Regenerate business summaries from your own PostgreSQL instance:
   ```bash
   python s1b_generate_summaries.py
   ```

4. Run the combined app:
   ```bash
   streamlit run app.py
   ```

## Files

**Analytics pipeline:**
- `schema.sql` — full PostgreSQL schema (9 tables, primary/foreign keys, constraints)
- `business_questions.sql` — SQL queries answering the four business questions
- `Ecommerce_pipeline.ipynb` — data cleaning, validation and loading pipeline
- `tableau exports/` — CSV exports of query results used to build the Tableau dashboard

**GenAI / RAG layer:**
- `s1_generate_summaries.py` — inspects database schema/tables
- `s1b_generate_summaries.py` — generates business summary chunks from PostgreSQL
- `summaries.json` — precomputed summaries (output of the script above)
- `app.py` — combined Streamlit app (Tableau dashboard + RAG chat interface)

## Dataset

[Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle)
