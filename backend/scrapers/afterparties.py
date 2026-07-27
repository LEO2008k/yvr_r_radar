from .base import BaseScraper
from typing import List, Dict
import datetime
import random
from .geocoder import get_lat_lng

class AfterpartiesScraper(BaseScraper):
    def scrape(self) -> List[Dict]:
        events = []
        try:
            from zoneinfo import ZoneInfo
            vancouver_tz = ZoneInfo("America/Vancouver")
        except ImportError:
            import pytz
            vancouver_tz = pytz.timezone("America/Vancouver")
            
        today_date = datetime.datetime.now(vancouver_tz).date()
        today_str = today_date.strftime('%Y-%m-%d')
        
        cities = ["vancouver", "burnaby", "richmond", "surrey"]
        titles = [
            "Tech Afterparty Networking",
            "Midnight Founders Drinks",
            "Post-Conference Mixer",
            "Hackathon Afterparty",
            "Web Devs Pub Crawl",
            "AI Summit After-drinks"
        ]
        
        for i in range(12):
            # Make random generation deterministic per day/index to avoid db duplicates
            random.seed(f"afterparty-{today_str}-{i}")
            
            city = random.choice(cities)
            address = city.capitalize()
            lat, lng = get_lat_lng(address)
            
            if lat is None or lng is None:
                continue
                
            # Randomize time between 21:00 and 02:00 next day
            start_hour = random.choice([21, 22, 23, 0, 1])
            start_time_str = f"{start_hour:02d}:00"
            if start_hour < 12:
                # Next day early morning
                event_date = today_date + datetime.timedelta(days=1)
                event_date_str = event_date.strftime('%Y-%m-%d')
            else:
                event_date_str = today_str
                
            end_hour = (start_hour + random.randint(2, 4)) % 24
            end_time_str = f"{end_hour:02d}:00"
            if end_hour < start_hour or end_hour < 12:
                end_date_str = (today_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                end_date_str = event_date_str
                
            events.append({
                "title": random.choice(titles),
                "time": f"{event_date_str} {start_time_str}",
                "end_time": f"{end_date_str} {end_time_str}",
                "lat": lat + random.uniform(-0.03, 0.03),
                "lng": lng + random.uniform(-0.03, 0.03),
                "address": address,
                "source": "Afterparty",
                "attendees_count": random.randint(30, 200),
                "event_url": "https://example.com/afterparty"
            })
            
        return events
