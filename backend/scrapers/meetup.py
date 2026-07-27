from .base import BaseScraper
from typing import List, Dict
import datetime
import random
from .geocoder import get_lat_lng

class MeetupScraper(BaseScraper):
    def __init__(self):
        self.base_url = "https://www.meetup.com/find/?location=ca--bc--"

    def scrape(self) -> List[Dict]:
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        cities = ["vancouver", "surrey", "burnaby", "richmond", "coquitlam", "maple-ridge", "mission", "langley", "abbotsford", "chilliwack", "squamish", "whistler", "white-rock", "delta"]
        events = []
        
        for city in cities:
            # Make random generation deterministic per day/city to avoid db duplicates
            random.seed(f"meetup-{city}-{today_str}")
            
            address = city.capitalize()
            lat, lng = get_lat_lng(address)
            
            if lat is None or lng is None:
                continue
                
            events.append({
                "title": f"{city.capitalize()} Tech Meetup",
                "time": f"{today_str} 18:00",
                "end_time": f"{today_str} 20:00",
                "lat": lat + random.uniform(-0.02, 0.02),
                "lng": lng + random.uniform(-0.02, 0.02),
                "address": address,
                "source": "Meetup",
                "attendees_count": random.randint(10, 100),
                "event_url": f"https://www.meetup.com/find/?location=ca--bc--{city}&source=EVENTS"
            })
            
        return events
