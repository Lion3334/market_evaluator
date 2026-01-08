-- Schema V2: Detailed Card Product & Sales Instance implementation

-- Drop existing tables to start fresh
DROP TABLE IF EXISTS forecasts;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS cards;
DROP TYPE IF EXISTS sport_type;

-- Enums
CREATE TYPE sport_type AS ENUM ('Basketball', 'Baseball', 'Football', 'Soccer', 'Hockey', 'TCG', 'Other');

-- 1. Base Product Table (The "Template")
CREATE TABLE cards (
    product_id SERIAL PRIMARY KEY,
    sport sport_type,
    year INT,
    manufacturer VARCHAR(50),
    set_name VARCHAR(100),
    subset_insert VARCHAR(100),
    player_name VARCHAR(100),
    card_number VARCHAR(50),
    team VARCHAR(100),
    
    -- Parallels & attributes
    parallel_type VARCHAR(100) DEFAULT 'Base',
    is_serial_numbered BOOLEAN DEFAULT FALSE,
    print_run INT, -- NULL if not numbered
    is_rookie_card BOOLEAN DEFAULT FALSE,
    is_autograph BOOLEAN DEFAULT FALSE,
    is_memorabilia BOOLEAN DEFAULT FALSE,
    variation_type VARCHAR(100),
    
    -- Internal
    epid VARCHAR(50), -- Keep EPID for linking if needed
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraint: Uniqueness of a specific card product
    UNIQUE(player_name, year, set_name, card_number, subset_insert, parallel_type, variation_type)
);

-- 2. Sales Instance Table (The "Transactions")
CREATE TABLE sales (
    sale_id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(100), -- eBay Item ID, etc.
    product_id INT REFERENCES cards(product_id) ON DELETE CASCADE,
    
    price DECIMAL(10, 2),
    sale_date TIMESTAMP,
    
    grader VARCHAR(50), -- PSA, BGS, SGC, Raw
    grade VARCHAR(20),  -- 10, 9, 8, Auth, etc.
    cert_number VARCHAR(100),
    
    source VARCHAR(50), -- eBay, PWCC, Goldin, SportsCardPro
    title TEXT, -- Original listing title
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(transaction_id, source) -- Prevent duplicate processing of same sale
);

-- 3. Forecasts (Updated to link to product_id)
CREATE TABLE forecasts (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES cards(product_id) ON DELETE CASCADE,
    forecast_price DECIMAL(10, 2),
    forecast_date DATE,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
