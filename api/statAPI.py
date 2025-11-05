from http.server import BaseHTTPRequestHandler
from playwright.sync_api import sync_playwright
import json
import os
from typing import Optional, Dict
from urllib.parse import urlparse, parse_qs

def scrape_java_heavy_site(profile_id: str) -> Optional[Dict[str, str]]:
    """
    Scrapes ONLY the BR Quads row from tracker.gg modes table.
    Returns a dict with the 6 values you want.
    """
    
    url = f"https://tracker.gg/bf6/profile/{profile_id}/modes"
    token = os.environ.get('BROWSERLESS_TOKEN')
    if not token:
        raise ValueError("BROWSERLESS_TOKEN environment variable is required")
    
    endpoint = f"wss://chrome.browserless.io/playwright?token={token}"
    
    with sync_playwright() as p:
        print("Connecting to remote browser...")
        browser = p.chromium.connect(endpoint)
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
                cell = tds[i] if i < len(tds) else None
                if cell:
                    main_span = cell.query_selector('span.stat-value span.truncate')
                    val = main_span.inner_text().strip() if main_span else "—"
                else:
                    val = "—"
                values.append(val)
            
            # Create result dict
            result = {
                "Value1": values[0],  # e.g., Time Played like 16h
                "Value2": values[1],  # e.g., Matches like 23
                "Value3": values[2],  # e.g., Win % like 44.2%
                "Value4": values[3],  # e.g., Kills like 52
                "Value5": values[4],  # e.g., Damage like 500
                "Value6": values[5],  # e.g., Assists like 304
            }
            
            return result
        
        except Exception as e:
            print(f"Error: {e}")
            return None
        
        finally:
            context.close()
            browser.close()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query params for profile_id (e.g., ?profile_id=3219760346)
        query = urlparse(self.path).query
        params = parse_qs(query)
        profile_id = params.get('profile_id', [None])[0]
        
        if not profile_id:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Missing profile_id query parameter')
            return None
        
        try:
            data = scrape_java_heavy_site(profile_id)
            if data:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode('utf-8'))
            else:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Scraping failed - BR Quads row not found or error occurred')
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode('utf-8'))
        
        return None  # Recommended for Vercel
