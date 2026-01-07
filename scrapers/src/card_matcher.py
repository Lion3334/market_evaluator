"""Card matching utilities.

Matches incoming data from various sources to canonical card records.
Uses fuzzy matching when exact identifiers aren't available.
"""

import re
from typing import Optional
from dataclasses import dataclass
from difflib import SequenceMatcher
from .db import execute_query


@dataclass
class MatchResult:
    """Result of a card matching attempt."""
    card_id: Optional[str]
    confidence: float  # 0.0 to 1.0
    match_method: str  # 'epid', 'cert', 'fuzzy', 'new'


def normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    text = text.lower()
    # Remove common noise words
    noise_words = ['the', 'a', 'an', 'card', 'rookie', 'rc', '#']
    for word in noise_words:
        text = text.replace(word, ' ')
    # Remove special characters
    text = re.sub(r'[^\w\s]', ' ', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_card_number(text: str) -> Optional[str]:
    """Extract card number from title or description."""
    # Common patterns: #123, No. 123, Card 123, /123
    patterns = [
        r'#\s*(\d+)',
        r'(?:no|card|number)\.?\s*(\d+)',
        r'/(\d+)',
        r'\b(\d{1,3})\b',  # Bare number (last resort)
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_grade(text: str) -> tuple[Optional[str], Optional[str]]:
    """Extract grade and grading company from title.
    
    Returns:
        Tuple of (condition_enum, grading_company) or (None, None)
    """
    # PSA grades
    psa_match = re.search(r'psa\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if psa_match:
        grade = psa_match.group(1)
        if '.' in grade:
            return f'PSA_{grade.replace(".", "_")}', 'PSA'
        return f'PSA_{grade}', 'PSA'
    
    # BGS grades
    bgs_match = re.search(r'bgs\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if bgs_match:
        grade = bgs_match.group(1)
        grade_key = grade.replace('.', '_')
        if grade == '10':
            return 'BGS_10', 'BGS'
        return f'BGS_{grade_key}', 'BGS'
    
    # SGC grades
    sgc_match = re.search(r'sgc\s*(\d+)', text, re.IGNORECASE)
    if sgc_match:
        return f'SGC_{sgc_match.group(1)}', 'SGC'
    
    # CGC grades
    cgc_match = re.search(r'cgc\s*(\d+)', text, re.IGNORECASE)
    if cgc_match:
        return f'CGC_{cgc_match.group(1)}', 'CGC'
    
    # Check for "raw" or ungraded
    if re.search(r'\braw\b|\bungraded\b', text, re.IGNORECASE):
        return 'RAW', None
    
    return None, None


def extract_parallel(text: str) -> Optional[str]:
    """Extract parallel/variant name from title."""
    # Common parallel patterns
    parallels = [
        # Numbered parallels
        r'/(\d+)',  # /10, /25, /99
        # Named parallels
        r'\b(gold|silver|bronze|platinum|ruby|sapphire|emerald|diamond)\b',
        r'\b(prizm|refractor|chrome|holo|holofoil)\b',
        r'\b(base|variation|variant|sp|ssp|parallel)\b',
        r'\b(mosaic|shimmer|camo|wave|velocity|lazer)\b',
        r'\b(1st edition|first edition|unlimited)\b',  # Pokemon
    ]
    
    found = []
    for pattern in parallels:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.extend(matches)
    
    if found:
        return ' '.join(found).title()
    return None


def similarity_score(s1: str, s2: str) -> float:
    """Calculate similarity score between two strings."""
    return SequenceMatcher(None, normalize_text(s1), normalize_text(s2)).ratio()


def match_card(
    title: str,
    year: Optional[int] = None,
    set_name: Optional[str] = None,
    card_number: Optional[str] = None,
    player_name: Optional[str] = None,
    epid: Optional[str] = None,
    cert_number: Optional[str] = None,
    category: str = 'SPORTS'
) -> MatchResult:
    """Match incoming data to a canonical card record.
    
    Uses multiple strategies in order of reliability:
    1. eBay EPID (exact match)
    2. PSA cert number (exact match)
    3. Fuzzy match on year + set + card number + player
    
    Returns MatchResult with card_id, confidence, and match method.
    """
    
    # Strategy 1: Match by EPID
    if epid:
        result = execute_query(
            "SELECT card_id FROM cards WHERE ebay_epid = %s",
            (epid,)
        )
        if result:
            return MatchResult(
                card_id=result[0]['card_id'],
                confidence=1.0,
                match_method='epid'
            )
    
    # Strategy 2: Match by cert number (from previous sales)
    if cert_number:
        result = execute_query(
            "SELECT card_id FROM sales WHERE cert_number = %s LIMIT 1",
            (cert_number,)
        )
        if result:
            return MatchResult(
                card_id=result[0]['card_id'],
                confidence=1.0,
                match_method='cert'
            )
    
    # Strategy 3: Fuzzy matching
    # Extract components if not provided
    if not card_number:
        card_number = extract_card_number(title)
    
    parallel = extract_parallel(title)
    
    # Build fuzzy match query
    query_parts = ["SELECT card_id, display_name FROM cards WHERE category = %s"]
    params = [category]
    
    if year:
        query_parts.append("AND set_id IN (SELECT set_id FROM sets WHERE year = %s)")
        params.append(year)
    
    if card_number:
        query_parts.append("AND card_number = %s")
        params.append(card_number)
    
    query = " ".join(query_parts) + " LIMIT 50"
    candidates = execute_query(query, tuple(params))
    
    if not candidates:
        # No matches found - this is a new card
        return MatchResult(card_id=None, confidence=0.0, match_method='new')
    
    # Score candidates by similarity
    best_match = None
    best_score = 0.0
    
    search_text = f"{player_name or ''} {set_name or ''} {parallel or ''} {title}"
    
    for candidate in candidates:
        score = similarity_score(search_text, candidate['display_name'])
        if score > best_score:
            best_score = score
            best_match = candidate
    
    if best_match and best_score >= 0.6:  # Threshold for acceptable match
        return MatchResult(
            card_id=best_match['card_id'],
            confidence=best_score,
            match_method='fuzzy'
        )
    
    # Low confidence - might be a new card
    return MatchResult(
        card_id=best_match['card_id'] if best_match else None,
        confidence=best_score,
        match_method='fuzzy_low_confidence'
    )


def create_card_from_listing(
    title: str,
    category: str,
    year: Optional[int] = None,
    set_name: Optional[str] = None,
    card_number: Optional[str] = None,
    player_name: Optional[str] = None,
    parallel: Optional[str] = None,
    epid: Optional[str] = None,
    image_url: Optional[str] = None
) -> Optional[str]:
    """Create a new card record from listing data.
    
    Returns the new card_id if successful.
    """
    # First, ensure set exists or create it
    if not set_name and not year:
        return None  # Can't create without set info
    
    set_result = execute_query(
        """
        INSERT INTO sets (category, year, name, normalized_name)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (category, year, name) DO UPDATE SET updated_at = NOW()
        RETURNING set_id
        """,
        (category, year or 0, set_name or 'Unknown', normalize_text(set_name or 'Unknown'))
    )
    
    if not set_result:
        return None
    
    set_id = set_result[0]['set_id']
    
    # Create display name
    parts = [str(year) if year else '', set_name or '', player_name or '', f'#{card_number}' if card_number else '']
    if parallel:
        parts.append(parallel)
    display_name = ' '.join(p for p in parts if p).strip()
    
    # Create card
    card_result = execute_query(
        """
        INSERT INTO cards (
            category, set_id, card_number, subject_name, 
            parallel_name, display_name, ebay_epid, image_url
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        RETURNING card_id
        """,
        (
            category,
            set_id,
            card_number or '',
            player_name or title[:100],
            parallel,
            display_name or title[:200],
            epid,
            image_url
        )
    )
    
    if card_result:
        return card_result[0]['card_id']
    return None
