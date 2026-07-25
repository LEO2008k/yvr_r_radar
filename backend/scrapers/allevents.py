from .base import BaseScraper
from typing import List, Dict
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from .geocoder import get_lat_lng

class AllEventsScraper(BaseScraper):
    def __init__(self):
        self.base_url = "https://allevents.in/vancouver/all"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def scrape(self) -> List[Dict]:
        events = []
        try:
            with httpx.Client(headers=self.headers, follow_redirects=True, timeout=15.0) as client:
                response = client.get(self.base_url)
                response.raise_for_status()
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all event cards
            event_cards = soup.find_all('li', class_='event-card event-card-link')
            
            for card in event_cards:
                title = card.get('data-name', '').strip()
                event_url = card.get('data-link', '').strip()
                
                if not title or not event_url:
                    continue
                    
                # Extract date and time
                date_div = card.find('div', class_='date')
                date_str = date_div.text.strip() if date_div else ""
                
                # Try to parse the date: "Sun, 20 Sep • 05:30 PM" or "Tue, 01 Dec • 06:00 PM + 3 more"
                time_iso = None
                try:
                    # Clean up string
                    clean_date = date_str.split('+')[0].strip() # Remove '+ X more'
                    clean_date = clean_date.replace('•', '-').strip()
                    # Now it looks like "Sun, 20 Sep - 05:30 PM"
                    
                    # Some might have year, some might not. Let's try multiple formats
                    import re
                    year = str(datetime.now().year)
                    if re.search(r'\d{4}', clean_date):
                        dt_obj = datetime.strptime(clean_date, "%a, %d %b, %Y - %I:%M %p")
                    else:
                        dt_obj = datetime.strptime(clean_date, "%a, %d %b - %I:%M %p")
                        dt_obj = dt_obj.replace(year=int(year))
                        
                    time_iso = dt_obj.strftime("%Y-%m-%d %H:%M")
                except Exception as e:
                    print(f"AllEvents: Failed to parse date '{date_str}': {e}")
                    continue
                
                # Extract location text
                location_div = card.find('div', class_='location')
                address = location_div.text.strip() if location_div else "Vancouver"
                
                # Geocode the address
                lat, lng = get_lat_lng(address)
                
                # If geocoding completely fails, fallback to a rough Vancouver center so it still shows up
                if lat is None or lng is None:
                    lat = 49.2827
                    lng = -123.1207
                    
                # Attendees count (Extract if available, otherwise default to something visual)
                attendees_count = 50
                interested_span = card.find('div', class_='interested')
                if interested_span:
                    interested_text = interested_span.text.strip()
                    import re
                    match = re.search(r'(\d+)', interested_text)
                    if match:
                        attendees_count = int(match.group(1)) * 3 # Inflate slightly to reflect actual attendance vs just 'interested' online
                
                events.append({
                    "title": title,
                    "time": time_iso,
                    "end_time": None, # AllEvents list page doesn't usually show end time clearly
                    "lat": lat,
                    "lng": lng,
                    "address": address,
                    "source": "AllEvents",
                    "attendees_count": attendees_count,
                    "event_url": event_url
                })
                
        except Exception as e:
            print(f"Error scraping AllEvents: {e}")
            
        return events
