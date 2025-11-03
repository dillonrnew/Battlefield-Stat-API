# scraper.py
from playwright.sync_api import sync_playwright
import csv
from typing import Optional, Dict


def scrape_java_heavy_site(url: str) -> Optional[Dict[str, str]]:
    """
    Scrapes ONLY the BR Quads row from tracker.gg modes table.
    Returns a dict with the 6 values you want.
    """
    
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
            ]
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        try:
            print(f"Loading: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for the BR Quads row specifically
            print("Waiting for BR Quads row...")
            page.wait_for_selector('span:has-text("BR Quads")', timeout=30000)
            page.wait_for_timeout(2000)
            
            # Save HTML for debugging
            html = page.content()
            with open("output.html", "w", encoding="utf-8") as f:
                f.write(html)
            
            # Find the BR Quads row
            br_quads_row = page.query_selector('tr:has(span:has-text("BR Quads"))')
            if not br_quads_row:
                print("BR Quads row not found!")
                return None
            
            # Get all td cells in this row
            tds = br_quads_row.query_selector_all('td[data-v-43859c7b]')
            
            # Extract the 6 values you want (skip mode name, take cells 1-6)
            values = []
            for i in range(1, 7):  # cells 1 through 6
                cell = tds[i]
                main_span = cell.query_selector('span.stat-value span.truncate')
                val = main_span.inner_text().strip() if main_span else "—"
                values.append(val)
            
            # Create result dict
            result = {
                "Value1": values[0],  # 16h
                "Value2": values[1],  # 23
                "Value3": values[2],  # 44.2%
                "Value4": values[3],  # 52
                "Value5": values[4],  # 500
                "Value6": values[5],  # 304
            }
            
            # PRINT THE RESULTS IMMEDIATELY
            print("\n=== BR QUADS DATA ===")
            print(f"Time Played: {result['Value1']}")
            print(f"Wins: {result['Value2']}")
            print(f"Win%: {result['Value3']}")
            print(f"Matches: {result['Value4']}")
            print(f"Kills: {result['Value5']}")
            print(f"Assists: {result['Value6']}")
            
            # Save to CSV (single row)
            with open("products.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Value1", "Value2", "Value3", "Value4", "Value5", "Value6"])
                writer.writerow(values)
            
            print("\nSuccess!")
            print("  HTML saved → output.html")
            print("  Data saved → products.csv")
            
            return result
            
        except Exception as e:
            print(f"Error: {e}")
            return None
        
        finally:
            context.close()
            browser.close()


# === RUN SCRAPER ===
if __name__ == "__main__":
    url = "https://tracker.gg/bf6/profile/3219760346/modes"
    result = scrape_java_heavy_site(url)
