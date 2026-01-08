-- Reset Schema ensuring 'id' based keys
DROP TABLE IF EXISTS forecasts;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS prices;
DROP TABLE IF EXISTS cards;

CREATE TABLE cards (
    id SERIAL PRIMARY KEY,
    player_name TEXT,
    year INTEGER,
    set_name TEXT,
    variant TEXT,
    card_number TEXT,
    is_rookie BOOLEAN DEFAULT FALSE,
    genre TEXT,
    base_set_name TEXT,
    epid TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_name, year, set_name, variant) -- Vital for ON CONFLICT
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    card_id INTEGER REFERENCES cards(id) ON DELETE CASCADE,
    price DECIMAL(10, 2),
    grade TEXT,
    date DATE,
    source TEXT,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE forecasts (
    id SERIAL PRIMARY KEY,
    card_id INTEGER REFERENCES cards(id) ON DELETE CASCADE,
    forecast_price DECIMAL(10, 2),
    forecast_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
