-- 1. Daily Supply Metrics (Upsert target)
CREATE TABLE IF NOT EXISTS daily_supply_metrics (
    date DATE NOT NULL,
    product_id INTEGER NOT NULL REFERENCES cards(product_id), -- Changed to INTEGER and FK
    new_count_fixed_price_only INTEGER DEFAULT 0,
    new_count_best_offer INTEGER DEFAULT 0,
    new_count_auction INTEGER DEFAULT 0,
    total_active_fixed_price_only INTEGER DEFAULT 0,
    total_active_best_offer INTEGER DEFAULT 0,
    total_active_auction INTEGER DEFAULT 0,
    median_new_price DECIMAL(10, 2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (product_id, date)
);

-- 2. Price History (The Output of our Model)
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    product_id INTEGER NOT NULL REFERENCES cards(product_id), -- Linked to specific card variant
    estimated_market_value DECIMAL(10, 2),
    model_version VARCHAR(50),      -- e.g. "v1_supply_velocity"
    used_implied_sales BOOLEAN,     -- Was the Disappearing Listings feature ON?
    supply_shock_multiplier DECIMAL(4, 2), -- What multiplier was used? (e.g. 1.5)
    signal_strength VARCHAR(50),    -- 'High', 'Medium', 'Low'
    driving_factor VARCHAR(100),    -- 'Floor', 'New Low', 'Implied Sale'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast retrieval of price history
CREATE INDEX IF NOT EXISTS idx_price_hist_pid_date ON price_history(product_id, date);

-- 3. Sentinel Validation Tables
-- Flag for Sentinel Cards (Already done? Safe to run again)
ALTER TABLE cards ADD COLUMN IF NOT EXISTS is_sentinel BOOLEAN DEFAULT FALSE;

-- Sentinel Sales (Ground Truth)
CREATE TABLE IF NOT EXISTS sentinel_sales (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES cards(product_id),
    sold_date DATE NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    source VARCHAR(50), -- 'SportsCardsPro', 'eBay'
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, sold_date, price) -- Basic deduping
);
