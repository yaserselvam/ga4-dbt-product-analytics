-- ============================================================================
-- Snowflake setup for the GA4 dbt port. Paste into a Snowflake worksheet on a
-- fresh trial (you start as ACCOUNTADMIN). Runs top to bottom.
-- Creates: warehouse, database GA4_DEMO, schemas RAW + ANALYTICS, a TRANSFORMER
-- role for dbt, and the RAW.EVENTS landing table (event_params etc. as VARIANT).
-- ============================================================================

-- 1. Warehouse (trial default is COMPUTE_WH; this is idempotent).
CREATE WAREHOUSE IF NOT EXISTS COMPUTE_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

-- 2. Database + schemas.
CREATE DATABASE IF NOT EXISTS GA4_DEMO;
CREATE SCHEMA IF NOT EXISTS GA4_DEMO.RAW;
CREATE SCHEMA IF NOT EXISTS GA4_DEMO.ANALYTICS;

-- 3. Role dbt will connect as, with just what it needs.
CREATE ROLE IF NOT EXISTS TRANSFORMER;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE TRANSFORMER;
GRANT USAGE ON DATABASE GA4_DEMO TO ROLE TRANSFORMER;
GRANT ALL ON SCHEMA GA4_DEMO.RAW TO ROLE TRANSFORMER;
GRANT ALL ON SCHEMA GA4_DEMO.ANALYTICS TO ROLE TRANSFORMER;
GRANT ALL ON FUTURE TABLES IN SCHEMA GA4_DEMO.RAW TO ROLE TRANSFORMER;
GRANT ALL ON FUTURE TABLES IN SCHEMA GA4_DEMO.ANALYTICS TO ROLE TRANSFORMER;
GRANT ALL ON FUTURE VIEWS IN SCHEMA GA4_DEMO.ANALYTICS TO ROLE TRANSFORMER;

-- Give yourself the role (replace with your trial username, shown top-right).
SET my_user = CURRENT_USER();
GRANT ROLE TRANSFORMER TO USER IDENTIFIER($my_user);

-- 4. Landing table. GA4 nested fields land as VARIANT; staging flattens them.
CREATE TABLE IF NOT EXISTS GA4_DEMO.RAW.EVENTS (
  event_date        STRING,      -- 'YYYYMMDD'
  event_timestamp   NUMBER,      -- micros since epoch
  event_name        STRING,
  user_pseudo_id    STRING,
  event_params      VARIANT,     -- array of {key, value:{string_value,int_value,...}}
  device            VARIANT,
  geo               VARIANT,
  traffic_source    VARIANT,
  ecommerce         VARIANT,
  items             VARIANT
);

-- Sanity check after you load data (step 2 of the runbook):
-- SELECT COUNT(*) FROM GA4_DEMO.RAW.EVENTS;
-- SELECT * FROM GA4_DEMO.RAW.EVENTS LIMIT 5;
