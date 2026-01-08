import httpx
from bs4 import BeautifulSoup

url = "https://www.sportscardspro.com/game/football-cards-2024-panini-donruss-downtown/drake-maye-13"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
resp = httpx.get(url, headers=headers)
soup = BeautifulSoup(resp.text, "html.parser")

# Dump full to file
with open("debug_sold.html", "w") as f:
    f.write(soup.prettify())

print("Dumped HTML to debug_sold.html")

# Search for identifiers in text
if "completed-auctions" in str(soup):
    print("Found 'completed-auctions' string in HTML")
else:
    print("'completed-auctions' NOT found in HTML")

