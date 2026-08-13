# Olist E-Commerce Analytics Pipeline

An end-to-end data analytics project using the Olist Brazilian E-Commerce dataset — from raw CSVs to a published interactive dashboard.

## Overview

This project builds a complete analytics pipeline: designing a normalized PostgreSQL schema, cleaning and loading ~120K real e-commerce orders, writing SQL to answer business questions, and visualizing insights in an interactive Tableau dashboard.

## Business Questions Answered

1. Which product categories drive the most revenue?
2. Does delivery time affect customer review scores?
3. What is the repeat purchase rate?
4. How does seller performance vary across revenue and ratings?

## Tech Stack

- **PostgreSQL** — relational schema design, data storage
- **Python (pandas, SQLAlchemy)** — data cleaning, transformation, and loading
- **SQL** — business question analysis (joins, aggregations, window functions)
- **Tableau Public** — interactive dashboard

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

## Dashboard

[View the interactive Tableau dashboard]
(https://public.tableau.com/app/profile/abhishek.ravikumar8688/viz/OlistE-CommerceAnalytics_17865833504340/OlistE-CommerceAnalyticsDashboard)

## Files

- `schema.sql` — full PostgreSQL schema (9 tables, primary/foreign keys, constraints)
- `business_questions.sql` — SQL queries answering the four business questions
- `Ecommerce_pipeline.ipynb` — data cleaning, validation, and loading pipeline
- `tableau exports/` - CSV exports of query results used to build the Tableau dashboard

## Dataset

[Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle)
