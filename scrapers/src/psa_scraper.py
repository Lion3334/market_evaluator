"""PSA Population scraper.

Scrapes PSA's pop report pages to get grading population data.
Uses BeautifulSoup for HTML parsing.
"""

import re
import time
import httpx
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class PSAPopulation:
    """Population data for a card from PSA."""
    card_name: str
    set_name: str
    year: int
    card_number: str
    grade_1: int = 0
    grade_1_5: int = 0
    grade_2: int = 0
    grade_3: int = 0
    grade_4: int = 0
    grade_5: int = 0
    grade_6: int = 0
    grade_7: int = 0
    grade_8: int = 0
    grade_9: int = 0
    grade_10: int = 0
    auth: int = 0
    total: int = 0
    source_url: str = ""
    
    @property
    def gem_rate(self) -> float:
        """Calculate gem rate (% of PSA 10s)."""
        if self.total == 0:
            return 0.0
        return (self.grade_10 / self.total) * 100


class PSAScraper:
    """Scraper for PSA population reports."""
    
    BASE_URL = "https://www.psacard.com"
    POP_SEARCH_URL = f"{BASE_URL}/pop"
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    def __init__(self, delay_ms: int = 2000):
        self.delay_ms = delay_ms
        self.client = httpx.Client(timeout=30.0, headers=self.HEADERS, follow_redirects=True)
        self._last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = (time.time() * 1000) - self._last_request_time
        if elapsed < self.delay_ms:
            time.sleep((self.delay_ms - elapsed) / 1000)
        self._last_request_time = time.time() * 1000
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def search_set(self, query: str, category: str = "Trading Cards") -> list[dict]:
        """Search for sets in PSA pop report.
        
        Args:
            query: Search query (e.g., "2024 Panini Mosaic")
            category: Category to search in
            
        Returns:
            List of matching sets with their pop report URLs
        """
        self._rate_limit()
        
        response = self.client.get(
            f"{self.POP_SEARCH_URL}",
            params={"q": query}
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        results = []
        
        # Parse search results - PSA's structure may vary
        # This is a template that needs adjustment based on actual HTML
        for row in soup.select('.pop-report-set, .search-result'):
            link = row.select_one('a')
            if link:
                results.append({
                    'name': link.get_text(strip=True),
                    'url': self.BASE_URL + link.get('href', ''),
                })
        
        return results
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def get_set_population(self, set_url: str) -> list[PSAPopulation]:
        """Get population data for all cards in a set.
        
        Args:
            set_url: Full URL to the set's pop report page
            
        Returns:
            List of PSAPopulation objects for each card variant
        """
        self._rate_limit()
        
        response = self.client.get(set_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        populations = []
        
        # Extract set info from page
        set_name = self._extract_set_name(soup)
        year = self._extract_year(soup)
        
        # Parse population table
        # PSA tables typically have columns: Card #, Name, Auth, 1, 1.5, 2, ... 10, Total
        table = soup.select_one('.pop-table, table.population')
        if not table:
            return populations
        
        for row in table.select('tbody tr'):
            cells = row.select('td')
            if len(cells) < 13:  # Need at least card#, name, auth, grades 1-10, total
                continue
            
            try:
                pop = PSAPopulation(
                    card_name=cells[1].get_text(strip=True),
                    set_name=set_name,
                    year=year,
                    card_number=cells[0].get_text(strip=True),
                    auth=self._parse_int(cells[2].get_text()),
                    grade_1=self._parse_int(cells[3].get_text()),
                    grade_1_5=self._parse_int(cells[4].get_text()),
                    grade_2=self._parse_int(cells[5].get_text()),
                    grade_3=self._parse_int(cells[6].get_text()),
                    grade_4=self._parse_int(cells[7].get_text()),
                    grade_5=self._parse_int(cells[8].get_text()),
                    grade_6=self._parse_int(cells[9].get_text()),
                    grade_7=self._parse_int(cells[10].get_text()),
                    grade_8=self._parse_int(cells[11].get_text()),
                    grade_9=self._parse_int(cells[12].get_text()),
                    grade_10=self._parse_int(cells[13].get_text()),
                    total=self._parse_int(cells[14].get_text()) if len(cells) > 14 else 0,
                    source_url=set_url
                )
                
                # Calculate total if not provided
                if pop.total == 0:
                    pop.total = (
                        pop.grade_1 + pop.grade_1_5 + pop.grade_2 + pop.grade_3 +
                        pop.grade_4 + pop.grade_5 + pop.grade_6 + pop.grade_7 +
                        pop.grade_8 + pop.grade_9 + pop.grade_10
                    )
                
                populations.append(pop)
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue
        
        return populations
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def lookup_cert(self, cert_number: str) -> Optional[dict]:
        """Look up a specific PSA certification number.
        
        Args:
            cert_number: PSA certification number
            
        Returns:
            Card details if found, None otherwise
        """
        self._rate_limit()
        
        response = self.client.get(
            f"{self.BASE_URL}/cert/{cert_number}"
        )
        
        if response.status_code == 404:
            return None
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Parse cert page - structure varies
        result = {
            'cert_number': cert_number,
            'grade': None,
            'card_name': None,
            'set_name': None,
            'year': None,
        }
        
        # Extract grade
        grade_el = soup.select_one('.grade, .cert-grade')
        if grade_el:
            grade_text = grade_el.get_text(strip=True)
            grade_match = re.search(r'(\d+(?:\.\d+)?)', grade_text)
            if grade_match:
                result['grade'] = float(grade_match.group(1))
        
        # Extract card info
        desc_el = soup.select_one('.description, .cert-description')
        if desc_el:
            result['card_name'] = desc_el.get_text(strip=True)
        
        return result
    
    def _extract_set_name(self, soup: BeautifulSoup) -> str:
        """Extract set name from pop report page."""
        title = soup.select_one('h1, .set-title')
        if title:
            return title.get_text(strip=True)
        return ""
    
    def _extract_year(self, soup: BeautifulSoup) -> int:
        """Extract year from pop report page."""
        title = soup.select_one('h1, .set-title')
        if title:
            year_match = re.search(r'(19|20)\d{2}', title.get_text())
            if year_match:
                return int(year_match.group())
        return 0
    
    def _parse_int(self, text: str) -> int:
        """Parse integer from text, handling commas and dashes."""
        text = text.strip().replace(',', '').replace('-', '0')
        try:
            return int(text)
        except ValueError:
            return 0
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
