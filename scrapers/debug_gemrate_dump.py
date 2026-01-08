import httpx
from bs4 import BeautifulSoup

URL = "https://www.gemrate.com/universal-search?query=2024+Topps+Cosmic+Caleb+Williams"

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    resp = httpx.get(URL, headers=headers, follow_redirects=True)
    soup = BeautifulSoup(resp.text, "lxml")
    
    scripts = soup.find_all('script')
    # We know it is likely the last large script, or index 17
    # But let's find the one with 'currentGemrateId' just to be safe
    
    target_script = None
    for script in scripts:
        if script.string and 'currentGemrateId' in script.string:
            target_script = script.string
            break
            
    if target_script:
        with open("scrapers/debug_script_17.js", "w") as f:
            f.write(target_script)
        print(f"Dumped {len(target_script)} chars to scrapers/debug_script_17.js")
    else:
        print("Target script not found.")

if __name__ == "__main__":
    main()
