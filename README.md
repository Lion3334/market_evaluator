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

## License

MIT
