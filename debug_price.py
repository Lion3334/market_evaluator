import httpx
from bs4 import BeautifulSoup
import re

url = "https://www.sportscardspro.com/game/football-cards-2024-panini-donruss-downtown/drake-maye-13"
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
resp = httpx.get(url, headers=headers)
soup = BeautifulSoup(resp.text, "html.parser")

ungraded = soup.select_one(".price-panel.ungraded .price")
print(f"Ungraded Tag: {ungraded}")
if ungraded:
    print(f"Text: {ungraded.text}")

psa10 = soup.select_one(".price-panel.psa_10 .price")
print(f"PSA10 Tag: {psa10}")
if psa10:
    print(f"Text: {psa10.text}")

# Dump full to file
with open("debug_page.html", "w") as f:
    f.write(soup.prettify())

# Search for price value
print("Searching for $1, in HTML...")
if "$1," in soup.text or "$1," in str(soup):
    print("Found price string!")
else:
    print("Price string NOT found.")
    
# Check for JSON data
scripts = soup.find_all("script")
for s in scripts:
    if "ungraded" in str(s):
        print("Found 'ungraded' in script!")

