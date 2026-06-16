-- TradeAI Database Initialization Script
-- This runs only on first postgres container start-up

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Grant all privileges to our user
GRANT ALL PRIVILEGES ON DATABASE tradeai_db TO tradeai;
