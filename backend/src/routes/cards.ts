import { Router, Request, Response } from 'express';
import { query } from '../db/index.js';
import { Card, CardDetail, PriceStats, Population, SearchResult } from '../types/index.js';

const router = Router();

// Search cards with autocomplete
router.get('/search', async (req: Request, res: Response) => {
    try {
        const { q, limit = 10 } = req.query;

        if (!q || typeof q !== 'string' || q.length < 2) {
            return res.json({ results: [] });
        }

        const searchQuery = `
      SELECT 
        c.card_id,
        s.display_text,
        s.popularity_score,
        c.category,
        sets.year,
        sets.name as set_name
      FROM search_index s
      JOIN cards c ON s.card_id = c.card_id
      JOIN sets ON c.set_id = sets.set_id
      WHERE s.search_vector @@ plainto_tsquery('english', $1)
         OR s.display_text ILIKE '%' || $1 || '%'
      ORDER BY 
        s.popularity_score DESC,
        ts_rank(s.search_vector, plainto_tsquery('english', $1)) DESC
      LIMIT $2
    `;

        const results = await query<SearchResult>(searchQuery, [q, Number(limit)]);
        return res.json({ results });
    } catch (error) {
        console.error('Search error:', error);
        return res.status(500).json({ error: 'Search failed' });
    }
});

// Get card details
router.get('/:cardId', async (req: Request, res: Response) => {
    try {
        const { cardId } = req.params;

        // Get card with set info
        const cardQuery = `
      SELECT 
        c.*,
        s.name as set_name,
        s.year,
        s.manufacturer
      FROM cards c
      JOIN sets s ON c.set_id = s.set_id
      WHERE c.card_id = $1
    `;

        const cards = await query<Card & { set_name: string; year: number; manufacturer?: string }>(
            cardQuery,
            [cardId]
        );

        if (cards.length === 0) {
            return res.status(404).json({ error: 'Card not found' });
        }

        const card = cards[0];

        // Get population data
        const popQuery = `
      SELECT * FROM population WHERE card_id = $1 AND grading_company = 'PSA'
    `;
        const population = await query<Population>(popQuery, [cardId]);

        // Get price stats
        const priceQuery = `
      SELECT * FROM card_price_stats WHERE card_id = $1
    `;
        const priceStats = await query<PriceStats>(priceQuery, [cardId]);

        // Get active listings count
        const listingsQuery = `
      SELECT COUNT(*) as count FROM listings WHERE card_id = $1 AND is_active = TRUE
    `;
        const listingsCount = await query<{ count: string }>(listingsQuery, [cardId]);

        // Calculate gem rate
        let gemRate: number | undefined;
        if (population.length > 0 && population[0].total_graded > 0) {
            gemRate = (population[0].grade_10 / population[0].total_graded) * 100;
        }

        const result: CardDetail = {
            ...card,
            gem_rate: gemRate,
            population: population[0],
            price_stats: priceStats,
            active_listings_count: Number(listingsCount[0]?.count || 0)
        };

        return res.json(result);
    } catch (error) {
        console.error('Get card error:', error);
        return res.status(500).json({ error: 'Failed to get card' });
    }
});

// Get card sales history
router.get('/:cardId/sales', async (req: Request, res: Response) => {
    try {
        const { cardId } = req.params;
        const { condition, limit = 100, offset = 0 } = req.query;

        let salesQuery = `
      SELECT * FROM sales 
      WHERE card_id = $1
    `;
        const params: unknown[] = [cardId];

        if (condition) {
            salesQuery += ` AND condition = $${params.length + 1}`;
            params.push(condition);
        }

        salesQuery += ` ORDER BY sale_date DESC LIMIT $${params.length + 1} OFFSET $${params.length + 2}`;
        params.push(Number(limit), Number(offset));

        const sales = await query(salesQuery, params);
        return res.json({ sales });
    } catch (error) {
        console.error('Get sales error:', error);
        return res.status(500).json({ error: 'Failed to get sales' });
    }
});

// Get card population/gem rate
router.get('/:cardId/population', async (req: Request, res: Response) => {
    try {
        const { cardId } = req.params;

        const popQuery = `
      SELECT 
        p.*,
        CASE 
          WHEN p.total_graded > 0 
          THEN ROUND(p.grade_10::numeric / p.total_graded * 100, 2)
          ELSE NULL 
        END as gem_rate
      FROM population p
      WHERE card_id = $1
    `;

        const population = await query(popQuery, [cardId]);

        // Get history
        const historyQuery = `
      SELECT * FROM population_history 
      WHERE card_id = $1 
      ORDER BY snapshot_date DESC 
      LIMIT 30
    `;
        const history = await query(historyQuery, [cardId]);

        return res.json({
            current: population[0] || null,
            history
        });
    } catch (error) {
        console.error('Get population error:', error);
        return res.status(500).json({ error: 'Failed to get population' });
    }
});

// Get active listings for card
router.get('/:cardId/listings', async (req: Request, res: Response) => {
    try {
        const { cardId } = req.params;
        const { condition, sort = 'ending_soon' } = req.query;

        let listingsQuery = `
      SELECT * FROM listings 
      WHERE card_id = $1 AND is_active = TRUE
    `;
        const params: unknown[] = [cardId];

        if (condition) {
            listingsQuery += ` AND condition = $${params.length + 1}`;
            params.push(condition);
        }

        // Sorting
        switch (sort) {
            case 'price_low':
                listingsQuery += ' ORDER BY current_price ASC';
                break;
            case 'price_high':
                listingsQuery += ' ORDER BY current_price DESC';
                break;
            case 'ending_soon':
            default:
                listingsQuery += ' ORDER BY end_time ASC NULLS LAST';
        }

        const listings = await query(listingsQuery, params);
        return res.json({ listings });
    } catch (error) {
        console.error('Get listings error:', error);
        return res.status(500).json({ error: 'Failed to get listings' });
    }
});

// Get deals (listings below market value)
router.get('/:cardId/deals', async (req: Request, res: Response) => {
    try {
        const { cardId } = req.params;

        const dealsQuery = `
      SELECT * FROM potential_deals WHERE card_id = $1
    `;

        const deals = await query(dealsQuery, [cardId]);
        return res.json({ deals });
    } catch (error) {
        console.error('Get deals error:', error);
        return res.status(500).json({ error: 'Failed to get deals' });
    }
});

export default router;
