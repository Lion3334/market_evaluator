-- Cards Table
CREATE TABLE IF NOT EXISTS cards (
    epid VARCHAR(50) PRIMARY KEY,
    player_name VARCHAR(100),
    year INTEGER,
    set_name VARCHAR(100),
    variant VARCHAR(100),
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transaction History Table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    card_epid VARCHAR(50) REFERENCES cards(epid),
    txn_date DATE NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    grade VARCHAR(20),
    source VARCHAR(50),
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Forecasts Table
CREATE TABLE IF NOT EXISTS forecasts (
    id SERIAL PRIMARY KEY,
    card_epid VARCHAR(50) REFERENCES cards(epid),
    forecast_date DATE DEFAULT CURRENT_DATE,
    target_date DATE,
    predicted_price DECIMAL(10, 2),
    confidence_score DECIMAL(5, 2),
    model_version VARCHAR(50),
    grade VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_txn_epid_date ON transactions(card_epid, txn_date);
CREATE INDEX idx_forecast_epid_date ON forecasts(card_epid, forecast_date);
