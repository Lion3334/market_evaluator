// Shared types for CardPulse

export type CardCategory = 'SPORTS' | 'POKEMON' | 'MAGIC_THE_GATHERING' | 'YUGIOH' | 'OTHER';

export type CardCondition =
    | 'RAW'
    | 'PSA_1' | 'PSA_1_5' | 'PSA_2' | 'PSA_3' | 'PSA_4' | 'PSA_5'
    | 'PSA_6' | 'PSA_7' | 'PSA_8' | 'PSA_9' | 'PSA_10'
    | 'BGS_7' | 'BGS_7_5' | 'BGS_8' | 'BGS_8_5' | 'BGS_9'
    | 'BGS_9_5' | 'BGS_10' | 'BGS_PRISTINE_10'
    | 'SGC_7' | 'SGC_8' | 'SGC_9' | 'SGC_10'
    | 'CGC_7' | 'CGC_8' | 'CGC_9' | 'CGC_10'
    | 'UNKNOWN';

export type GradingCompany = 'PSA' | 'BGS' | 'SGC' | 'CGC' | 'OTHER';

export type ListingType = 'AUCTION' | 'BUY_IT_NOW' | 'BEST_OFFER' | 'AUCTION_WITH_BIN';

export type DataSource = 'EBAY' | 'PWCC' | 'GOLDIN' | '130POINT' | 'PSA_POP' | 'GEMRATE' | 'MANUAL';

// Card entity
export interface Card {
    card_id: string;
    category: CardCategory;
    set_id: string;
    card_number: string;
    player_id?: string;
    pokemon_id?: string;
    subject_name: string;
    parallel_id?: string;
    parallel_name?: string;
    ebay_epid?: string;
    psa_cert_prefix?: string;
    display_name: string;
    image_url?: string;
    is_rookie: boolean;
    is_autograph: boolean;
    is_memorabilia: boolean;
    created_at: Date;
    updated_at: Date;
}

// Set entity
export interface CardSet {
    set_id: string;
    category: CardCategory;
    year: number;
    name: string;
    normalized_name: string;
    manufacturer?: string;
    release_date?: Date;
}

// Sale record
export interface Sale {
    sale_id: string;
    card_id: string;
    source: DataSource;
    source_item_id?: string;
    sale_price: number;
    sale_date: Date;
    condition: CardCondition;
    grading_company?: GradingCompany;
    cert_number?: string;
    listing_title?: string;
    shipping_cost?: number;
    seller_id?: string;
}

// Population data
export interface Population {
    pop_id: string;
    card_id: string;
    grading_company: GradingCompany;
    grade_1: number;
    grade_1_5: number;
    grade_2: number;
    grade_3: number;
    grade_4: number;
    grade_5: number;
    grade_6: number;
    grade_7: number;
    grade_8: number;
    grade_9: number;
    grade_10: number;
    grade_auth: number;
    total_graded: number;
    source_url?: string;
    last_updated: Date;
}

// Active listing
export interface Listing {
    listing_id: string;
    card_id: string;
    source: DataSource;
    source_item_id: string;
    listing_type: ListingType;
    current_price: number;
    buy_now_price?: number;
    starting_price?: number;
    shipping_cost?: number;
    condition: CardCondition;
    grading_company?: GradingCompany;
    cert_number?: string;
    listing_title: string;
    listing_url: string;
    image_urls?: string[];
    seller_id?: string;
    seller_name?: string;
    seller_rating?: number;
    seller_feedback_count?: number;
    bid_count: number;
    watcher_count: number;
    start_time?: Date;
    end_time?: Date;
    is_active: boolean;
    first_seen: Date;
    last_updated: Date;
}

// Price statistics (from materialized view)
export interface PriceStats {
    card_id: string;
    condition: CardCondition;
    total_sales: number;
    avg_price: number;
    median_price: number;
    min_price: number;
    max_price: number;
    price_stddev?: number;
    avg_price_30d?: number;
    avg_price_90d?: number;
    sales_30d: number;
    sales_90d: number;
    last_sale_date?: Date;
}

// Search result
export interface SearchResult {
    card_id: string;
    display_text: string;
    popularity_score: number;
    category: CardCategory;
    year?: number;
    set_name?: string;
}

// Card detail (combined view for card page)
export interface CardDetail extends Card {
    set_name: string;
    year: number;
    manufacturer?: string;
    gem_rate?: number;
    population?: Population;
    price_stats: PriceStats[];
    active_listings_count: number;
}

// Potential deal
export interface Deal {
    listing_id: string;
    card_id: string;
    display_name: string;
    listing_type: ListingType;
    current_price: number;
    condition: CardCondition;
    listing_url: string;
    end_time?: Date;
    bid_count: number;
    market_value: number;
    potential_savings: number;
    discount_pct: number;
}
