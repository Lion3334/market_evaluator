-- Tiered Refresh Schema Updates

-- 1. Add refresh scheduling columns to cards table
ALTER TABLE cards ADD COLUMN IF NOT EXISTS refresh_tier INTEGER DEFAULT 4;
ALTER TABLE cards ADD COLUMN IF NOT EXISTS last_refreshed_at TIMESTAMP;
ALTER TABLE cards ADD COLUMN IF NOT EXISTS next_refresh_due DATE;

-- 2. Add disappearance tracking columns to active_listings table
ALTER TABLE active_listings ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE active_listings ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE active_listings ADD COLUMN IF NOT EXISTS disappeared_at TIMESTAMP;

-- 3. Create index for efficient refresh queries
CREATE INDEX IF NOT EXISTS idx_cards_next_refresh ON cards(next_refresh_due) WHERE next_refresh_due IS NOT NULL;

-- 4. Create index for efficient active listing queries
CREATE INDEX IF NOT EXISTS idx_listings_active ON active_listings(product_id, is_active) WHERE is_active = TRUE;

-- 5. Create index for disappearance analysis
CREATE INDEX IF NOT EXISTS idx_listings_disappeared ON active_listings(product_id, disappeared_at) WHERE disappeared_at IS NOT NULL;
