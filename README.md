# CardPulse - Trading Card Market Analysis

A web application for tracking trading card market data, including historical sales, gem rates, and live auctions.

## Features

- 🔍 **Card Search** - Autocomplete search across sports and Pokémon cards
- 📊 **Historical Sales** - Track completed sales from eBay
- 💎 **Gem Rate Data** - PSA population and gem rate tracking
- 🔴 **Live Auctions** - Monitor active listings and find deals

## Tech Stack

- **Database**: PostgreSQL 15+
- **Backend**: Node.js with Express
- **Frontend**: Next.js / React
- **ETL**: Python scrapers with scheduling

## Project Structure

```
cardpulse/
├── database/           # SQL schemas and migrations
├── backend/            # Node.js API server
├── frontend/           # Next.js web app
├── scrapers/           # Python data collectors
└── shared/             # Shared types and utilities
```

## Getting Started

### Prerequisites

- Node.js 18+
- PostgreSQL 15+
- Python 3.10+
- eBay Developer API credentials

### Database Setup

```bash
# Create database
createdb cardpulse

# Run migrations
cd database
psql -d cardpulse -f schema/001_initial_schema.sql
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

```
DATABASE_URL=postgresql://localhost:5432/cardpulse
EBAY_APP_ID=your_app_id
EBAY_CERT_ID=your_cert_id
EBAY_DEV_ID=your_dev_id
```


## Data Sourcing Strategy

### The eBay API Challenge
Initially, we aimed to source all historical sales data via the eBay Developer API. However, we encountered severe limitations in the Sandbox environment, including:
1.  **Rate Limits:** Strict caps on calls per day made bulk historical backfilling impossible.
2.  **Data Quality:** The Sandbox environment returned incomplete or mock data that did not reflect real-world price trends.
3.  **Search Constraints:** Keyword search relevance was poor compared to the public website.

### The Solution: SportsCardPro Scraping
To build a robust dataset, we pivoted to **Scraping SportsCardPro (SCP)** as our primary source of truth for historical sales.
*   **Granularity:** We parse specific HTML tables to distinguish between `Raw`, `PSA 9`, and `PSA 10` sales.
*   **Volume:** We successfully backfilled over 1,500 transactions for key players like Jayden Daniels.
*   **Reliability:** SCP aggregates verified eBay sales, filtering out noise better than raw API responses.

## Predictive Modeling: "Dual Forecast System"

We have developed a custom Machine Learning pipeline (`scrapers/train_model.py`) that generates a **Continuous Dual Forecast** for every card.

### 1. The Dual Output
The API (`GET /forecast`) returns two distinct signals:
*   **Price Target ($):** A regression model predicts the specific fair market value for the *next* transaction.
*   **Directional Signal (Bull/Bear):** A classification model predicts the *probability* that the next sale will be higher/lower than the last.

### 2. Key Features
Our Gradient Boosting models utilize advanced market dynamics:
*   **Staleness (`days_since_last_sale`):** The model learns how price "decays" or "drifts" during periods of inactivity.
*   **Spillover (Cross-Variant Heat):** If a player's high-end cards (e.g., Gold Prizms) surge, the model detects the "Player Heat" (`player_7d_vol`) and predicts a catch-up rally for their Base cards before it happens.
*   **Strict Daily Lags:** To prevent data leakage, we enforce strict T-1 information barriers. The model only "sees" data from yesterday's close.

### 3. Performance (Early Results)
On our pilot dataset (Jayden Daniels Downtown):
*   **Price Error (MAE):** ~$69 (approx. 10% variance on volatile cards).
*   **Directional Accuracy:** **85%**. The model correctly predicted the market movement (Up/Down) in 23 of the last 27 validations.

## License

MIT
