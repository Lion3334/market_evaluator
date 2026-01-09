
-- 1. Create Daily Model Performance Table (Aggregate Stats)
CREATE TABLE IF NOT EXISTS daily_model_performance (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    rmse DECIMAL(10, 4),      -- Root Mean Square Error
    mae DECIMAL(10, 4),       -- Mean Absolute Error
    bias DECIMAL(10, 4),      -- Mean Error (Bias)
    mape DECIMAL(5, 2),       -- Mean Absolute Percentage Error
    sentinel_count INTEGER,   -- How many sentinels were validated?
    hit_rate DECIMAL(5, 2),   -- % of estimates within 15% error
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, model_version)
);

-- 2. Enhance Price History for Per-Card Validation
ALTER TABLE price_history 
ADD COLUMN IF NOT EXISTS actual_sold_price DECIMAL(10, 2), -- Ground Truth from Sentinel Sales
ADD COLUMN IF NOT EXISTS error_pct DECIMAL(10, 2);         -- (Est - Actual) / Actual * 100
