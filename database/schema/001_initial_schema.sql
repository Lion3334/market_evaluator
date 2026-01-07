-- CardPulse Database Schema
-- Version: 001 - Initial Schema
-- Description: Core tables for trading card market analysis

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- ============================================================================
-- ENUM TYPES
-- ============================================================================

-- Card category (extensible for future card types)
CREATE TYPE card_category AS ENUM (
    'SPORTS',
    'POKEMON',
    'MAGIC_THE_GATHERING',
    'YUGIOH',
    'OTHER'
);

-- Card condition/grade
-- Designed for PSA initially, but structured to support other graders
CREATE TYPE card_condition AS ENUM (
    'RAW',
    -- PSA Grades
    'PSA_1', 'PSA_1_5', 'PSA_2', 'PSA_3', 'PSA_4', 'PSA_5',
    'PSA_6', 'PSA_7', 'PSA_8', 'PSA_9', 'PSA_10',
    -- BGS Grades (for future)
    'BGS_7', 'BGS_7_5', 'BGS_8', 'BGS_8_5', 'BGS_9', 
    'BGS_9_5', 'BGS_10', 'BGS_PRISTINE_10',
    -- SGC Grades (for future)
    'SGC_7', 'SGC_8', 'SGC_9', 'SGC_10',
    -- CGC Grades (for future)
    'CGC_7', 'CGC_8', 'CGC_9', 'CGC_10',
    'UNKNOWN'
);

-- Grading company
CREATE TYPE grading_company AS ENUM (
    'PSA',
    'BGS',
    'SGC',
    'CGC',
    'OTHER'
);

-- Listing type for auctions
CREATE TYPE listing_type AS ENUM (
    'AUCTION',
    'BUY_IT_NOW',
    'BEST_OFFER',
    'AUCTION_WITH_BIN'
);

-- Data source
CREATE TYPE data_source AS ENUM (
    'EBAY',
    'PWCC',
    'GOLDIN',
    '130POINT',
    'PSA_POP',
    'GEMRATE',
    'MANUAL'
);

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Sports/Teams/Leagues (for sports cards)
CREATE TABLE sports (
    sport_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,  -- 'Football', 'Basketball', 'Baseball', etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Players (for sports cards)
CREATE TABLE players (
    player_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,  -- Lowercase, no accents for search
    sport_id UUID REFERENCES sports(sport_id),
    team VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_players_normalized_name ON players(normalized_name);
CREATE INDEX idx_players_name_trgm ON players USING GIN(normalized_name gin_trgm_ops);

-- Pokemon Characters (for Pokemon cards)
CREATE TABLE pokemon (
    pokemon_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    pokedex_number INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_pokemon_normalized_name ON pokemon(normalized_name);
CREATE INDEX idx_pokemon_name_trgm ON pokemon USING GIN(normalized_name gin_trgm_ops);

-- Card Sets
CREATE TABLE sets (
    set_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category card_category NOT NULL,
    year INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    manufacturer VARCHAR(100),  -- 'Panini', 'Topps', 'Pokemon Company', etc.
    release_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(category, year, name)
);

CREATE INDEX idx_sets_year ON sets(year);
CREATE INDEX idx_sets_category ON sets(category);
CREATE INDEX idx_sets_name_trgm ON sets USING GIN(normalized_name gin_trgm_ops);

-- Parallels/Variants
CREATE TABLE parallels (
    parallel_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    set_id UUID REFERENCES sets(set_id),
    name VARCHAR(255) NOT NULL,
    normalized_name VARCHAR(255) NOT NULL,
    print_run INT,  -- e.g., 10, 25, 99, NULL for unlimited
    is_serial_numbered BOOLEAN DEFAULT FALSE,
    rarity_tier INT DEFAULT 0,  -- Higher = rarer (for sorting)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(set_id, name)
);

CREATE INDEX idx_parallels_set ON parallels(set_id);

-- Master Card Table
CREATE TABLE cards (
    card_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Core identifiers
    category card_category NOT NULL,
    set_id UUID NOT NULL REFERENCES sets(set_id),
    card_number VARCHAR(50) NOT NULL,  -- Card number within set
    
    -- Subject (one of these will be set based on category)
    player_id UUID REFERENCES players(player_id),
    pokemon_id UUID REFERENCES pokemon(pokemon_id),
    subject_name VARCHAR(255) NOT NULL,  -- Denormalized for search performance
    
    -- Variant info
    parallel_id UUID REFERENCES parallels(parallel_id),
    parallel_name VARCHAR(255),  -- Denormalized: 'Base', 'Gold /10', 'Prizm Silver', etc.
    
    -- External identifiers for matching
    ebay_epid VARCHAR(100),
    psa_cert_prefix VARCHAR(100),  -- For PSA lookup
    
    -- Display info
    display_name VARCHAR(500),  -- Full formatted name for display
    image_url VARCHAR(500),
    
    -- Metadata
    is_rookie BOOLEAN DEFAULT FALSE,
    is_autograph BOOLEAN DEFAULT FALSE,
    is_memorabilia BOOLEAN DEFAULT FALSE,  -- Patch/relic cards
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(set_id, card_number, COALESCE(parallel_id, '00000000-0000-0000-0000-000000000000'::UUID))
);

CREATE INDEX idx_cards_set ON cards(set_id);
CREATE INDEX idx_cards_player ON cards(player_id) WHERE player_id IS NOT NULL;
CREATE INDEX idx_cards_pokemon ON cards(pokemon_id) WHERE pokemon_id IS NOT NULL;
CREATE INDEX idx_cards_epid ON cards(ebay_epid) WHERE ebay_epid IS NOT NULL;
CREATE INDEX idx_cards_category ON cards(category);
CREATE INDEX idx_cards_subject_trgm ON cards USING GIN(subject_name gin_trgm_ops);

-- ============================================================================
-- HISTORICAL SALES DATA
-- ============================================================================

CREATE TABLE sales (
    sale_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_id UUID NOT NULL REFERENCES cards(card_id),
    
    -- Source info
    source data_source NOT NULL,
    source_item_id VARCHAR(100),  -- Original listing ID from source
    
    -- Sale details
    sale_price DECIMAL(10, 2) NOT NULL,
    sale_date TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Condition
    condition card_condition NOT NULL,
    grading_company grading_company,
    cert_number VARCHAR(50),  -- PSA/BGS cert number
    
    -- Listing info
    listing_title TEXT,
    shipping_cost DECIMAL(10, 2),
    seller_id VARCHAR(100),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(source, source_item_id)
);

CREATE INDEX idx_sales_card ON sales(card_id);
CREATE INDEX idx_sales_card_condition ON sales(card_id, condition);
CREATE INDEX idx_sales_date ON sales(sale_date DESC);
CREATE INDEX idx_sales_cert ON sales(cert_number) WHERE cert_number IS NOT NULL;

-- ============================================================================
-- PSA POPULATION / GEM RATE DATA
-- ============================================================================

CREATE TABLE population (
    pop_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_id UUID NOT NULL REFERENCES cards(card_id),
    grading_company grading_company NOT NULL DEFAULT 'PSA',
    
    -- Grade counts (PSA 1-10)
    grade_1 INT DEFAULT 0,
    grade_1_5 INT DEFAULT 0,
    grade_2 INT DEFAULT 0,
    grade_3 INT DEFAULT 0,
    grade_4 INT DEFAULT 0,
    grade_5 INT DEFAULT 0,
    grade_6 INT DEFAULT 0,
    grade_7 INT DEFAULT 0,
    grade_8 INT DEFAULT 0,
    grade_9 INT DEFAULT 0,
    grade_10 INT DEFAULT 0,
    
    -- Qualifiers (for PSA)
    grade_auth INT DEFAULT 0,  -- Authentic (trimmed, altered, etc.)
    
    -- Computed fields (updated by trigger)
    total_graded INT GENERATED ALWAYS AS (
        grade_1 + grade_1_5 + grade_2 + grade_3 + grade_4 + grade_5 +
        grade_6 + grade_7 + grade_8 + grade_9 + grade_10
    ) STORED,
    
    -- Source info
    source_url VARCHAR(500),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(card_id, grading_company)
);

CREATE INDEX idx_population_card ON population(card_id);

-- Population history for tracking changes over time
CREATE TABLE population_history (
    history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_id UUID NOT NULL REFERENCES cards(card_id),
    grading_company grading_company NOT NULL,
    snapshot_date DATE NOT NULL,
    
    -- Store full snapshot as JSON for flexibility
    population_data JSONB NOT NULL,
    total_graded INT,
    gem_rate DECIMAL(5, 2),  -- Percentage of 10s
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(card_id, grading_company, snapshot_date)
);

CREATE INDEX idx_pop_history_card ON population_history(card_id);
CREATE INDEX idx_pop_history_date ON population_history(snapshot_date DESC);

-- ============================================================================
-- LIVE LISTINGS / AUCTIONS
-- ============================================================================

CREATE TABLE listings (
    listing_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_id UUID NOT NULL REFERENCES cards(card_id),
    
    -- Source info
    source data_source NOT NULL,
    source_item_id VARCHAR(100) NOT NULL,
    
    -- Listing type
    listing_type listing_type NOT NULL,
    
    -- Pricing
    current_price DECIMAL(10, 2) NOT NULL,
    buy_now_price DECIMAL(10, 2),
    starting_price DECIMAL(10, 2),
    shipping_cost DECIMAL(10, 2),
    
    -- Condition
    condition card_condition NOT NULL,
    grading_company grading_company,
    cert_number VARCHAR(50),
    
    -- Listing details
    listing_title TEXT NOT NULL,
    listing_url VARCHAR(500) NOT NULL,
    image_urls TEXT[],
    
    -- Seller info
    seller_id VARCHAR(100),
    seller_name VARCHAR(255),
    seller_rating DECIMAL(5, 2),
    seller_feedback_count INT,
    
    -- Auction stats
    bid_count INT DEFAULT 0,
    watcher_count INT DEFAULT 0,
    
    -- Timing
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Tracking
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(source, source_item_id)
);

CREATE INDEX idx_listings_card ON listings(card_id);
CREATE INDEX idx_listings_active ON listings(card_id, is_active, condition) WHERE is_active = TRUE;
CREATE INDEX idx_listings_ending ON listings(end_time) WHERE is_active = TRUE;
CREATE INDEX idx_listings_source_item ON listings(source, source_item_id);

-- Price history for tracking bid progression
CREATE TABLE listing_price_history (
    history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id UUID NOT NULL REFERENCES listings(listing_id) ON DELETE CASCADE,
    price DECIMAL(10, 2) NOT NULL,
    bid_count INT,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_listing_price_history ON listing_price_history(listing_id);

-- ============================================================================
-- SEARCH & AUTOCOMPLETE
-- ============================================================================

CREATE TABLE search_index (
    card_id UUID PRIMARY KEY REFERENCES cards(card_id) ON DELETE CASCADE,
    
    -- Full-text search vector
    search_vector TSVECTOR NOT NULL,
    
    -- Display text for autocomplete dropdown
    display_text VARCHAR(500) NOT NULL,
    
    -- Ranking factors
    popularity_score INT DEFAULT 0,  -- Based on sales volume, searches
    last_sale_date TIMESTAMP WITH TIME ZONE,
    total_sales INT DEFAULT 0,
    avg_price DECIMAL(10, 2),
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_search_vector ON search_index USING GIN(search_vector);
CREATE INDEX idx_search_popularity ON search_index(popularity_score DESC);

-- ============================================================================
-- MATERIALIZED VIEWS FOR ANALYTICS
-- ============================================================================

-- Pre-computed price statistics per card/condition
CREATE MATERIALIZED VIEW card_price_stats AS
SELECT 
    card_id,
    condition,
    COUNT(*) as total_sales,
    AVG(sale_price) as avg_price,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sale_price) as median_price,
    MIN(sale_price) as min_price,
    MAX(sale_price) as max_price,
    STDDEV(sale_price) as price_stddev,
    AVG(sale_price) FILTER (WHERE sale_date > NOW() - INTERVAL '30 days') as avg_price_30d,
    AVG(sale_price) FILTER (WHERE sale_date > NOW() - INTERVAL '90 days') as avg_price_90d,
    COUNT(*) FILTER (WHERE sale_date > NOW() - INTERVAL '30 days') as sales_30d,
    COUNT(*) FILTER (WHERE sale_date > NOW() - INTERVAL '90 days') as sales_90d,
    MAX(sale_date) as last_sale_date
FROM sales
GROUP BY card_id, condition;

CREATE UNIQUE INDEX idx_price_stats_card_condition ON card_price_stats(card_id, condition);

-- Refresh function (call periodically)
CREATE OR REPLACE FUNCTION refresh_price_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY card_price_stats;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- HELPER VIEWS
-- ============================================================================

-- Deal detection: listings below market value
CREATE VIEW potential_deals AS
SELECT 
    l.listing_id,
    l.card_id,
    c.display_name,
    l.listing_type,
    l.current_price,
    l.condition,
    l.listing_url,
    l.end_time,
    l.bid_count,
    s.avg_price_90d as market_value,
    s.avg_price_90d - l.current_price as potential_savings,
    CASE 
        WHEN s.avg_price_90d > 0 
        THEN ROUND((s.avg_price_90d - l.current_price) / s.avg_price_90d * 100, 1)
        ELSE 0 
    END as discount_pct
FROM listings l
JOIN cards c ON l.card_id = c.card_id
LEFT JOIN card_price_stats s ON l.card_id = s.card_id AND l.condition = s.condition
WHERE l.is_active = TRUE
  AND s.avg_price_90d IS NOT NULL
  AND l.current_price < s.avg_price_90d * 0.8  -- At least 20% below market
ORDER BY discount_pct DESC;

-- Card summary view (combines all data for card detail page)
CREATE VIEW card_summary AS
SELECT 
    c.*,
    s.name as set_name,
    s.year,
    s.manufacturer,
    p.total_graded,
    CASE 
        WHEN p.total_graded > 0 
        THEN ROUND(p.grade_10::numeric / p.total_graded * 100, 2)
        ELSE NULL 
    END as gem_rate,
    ps.avg_price_90d as avg_price_raw,
    ps10.avg_price_90d as avg_price_psa10,
    (SELECT COUNT(*) FROM listings WHERE card_id = c.card_id AND is_active = TRUE) as active_listings
FROM cards c
JOIN sets s ON c.set_id = s.set_id
LEFT JOIN population p ON c.card_id = p.card_id AND p.grading_company = 'PSA'
LEFT JOIN card_price_stats ps ON c.card_id = ps.card_id AND ps.condition = 'RAW'
LEFT JOIN card_price_stats ps10 ON c.card_id = ps10.card_id AND ps10.condition = 'PSA_10';

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update search index when card is inserted/updated
CREATE OR REPLACE FUNCTION update_search_index()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO search_index (card_id, search_vector, display_text, popularity_score)
    VALUES (
        NEW.card_id,
        to_tsvector('english', 
            COALESCE(NEW.subject_name, '') || ' ' ||
            COALESCE(NEW.parallel_name, '') || ' ' ||
            COALESCE(NEW.display_name, '')
        ),
        NEW.display_name,
        0
    )
    ON CONFLICT (card_id) DO UPDATE SET
        search_vector = EXCLUDED.search_vector,
        display_text = EXCLUDED.display_text,
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_search_index
AFTER INSERT OR UPDATE ON cards
FOR EACH ROW
EXECUTE FUNCTION update_search_index();

-- Update card updated_at timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_cards_updated
BEFORE UPDATE ON cards
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trg_sets_updated
BEFORE UPDATE ON sets
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Insert common sports
INSERT INTO sports (name) VALUES 
    ('Football'),
    ('Basketball'),
    ('Baseball'),
    ('Hockey'),
    ('Soccer')
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE cards IS 'Master card table - the central entity for joining all data';
COMMENT ON TABLE sales IS 'Historical completed sales from eBay and other sources';
COMMENT ON TABLE population IS 'Current PSA (and future BGS/SGC) population counts';
COMMENT ON TABLE listings IS 'Active marketplace listings for deal monitoring';
COMMENT ON TABLE search_index IS 'Optimized search index for card autocomplete';
COMMENT ON MATERIALIZED VIEW card_price_stats IS 'Pre-computed price analytics - refresh periodically';
