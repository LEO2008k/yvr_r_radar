from .base import BaseScraper
from typing import List, Dict
import datetime
import random

class BCFerriesScraper(BaseScraper):
    def scrape(self) -> List[Dict]:
        events = []
        try:
            from zoneinfo import ZoneInfo
            vancouver_tz = ZoneInfo("America/Vancouver")
        except ImportError:
            import pytz
            vancouver_tz = pytz.timezone("America/Vancouver")
            
        today = datetime.datetime.now(vancouver_tz).date()
        
        terminals = [
            {
                "name": "Tsawwassen Ferry Terminal",
                "lat": 49.0084,
                "lng": -123.1281,
                "destinations": ["Victoria (Swartz Bay)", "Nanaimo (Duke Point)"]
            },
            {
                "name": "Horseshoe Bay Ferry Terminal",
                "lat": 49.3742,
                "lng": -123.2728,
                "destinations": ["Nanaimo (Departure Bay)", "Sunshine Coast (Langdale)"]
            }
        ]
        
        # Generate some mock arrivals and departures for today and the next few days
        for day_offset in range(0, 3):
            target_date = today + datetime.timedelta(days=day_offset)
            date_str = target_date.strftime('%Y-%m-%d')
            
            for terminal in terminals:
                # 5 arrivals and 5 departures per terminal per day
                for _ in range(5):
                    # Arrival
                    arr_hour = random.randint(7, 22)
                    arr_min = random.choice([0, 15, 30, 45])
                    dest = random.choice(terminal["destinations"])
                    
                    events.append({
                        "title": f"Ferry Arrival from {dest}",
                        "time": f"{date_str} {arr_hour:02d}:{arr_min:02d}",
                        "end_time": f"{date_str} {(arr_hour):02d}:{arr_min+30 if arr_min < 30 else arr_min-30:02d}",
                        "lat": terminal["lat"],
                        "lng": terminal["lng"],
                        "address": terminal["name"],
                        "source": "BCFerries",
                        "attendees_count": random.randint(150, 400), # Passengers
                        "event_url": "https://www.bcferries.com/current-conditions"
                    })
                    
                    # Departure
                    dep_hour = random.randint(7, 22)
                    dep_min = random.choice([0, 15, 30, 45])
                    dest_dep = random.choice(terminal["destinations"])
                    
                    events.append({
                        "title": f"Ferry Departure to {dest_dep}",
                        "time": f"{date_str} {dep_hour:02d}:{dep_min:02d}",
                        "end_time": f"{date_str} {(dep_hour):02d}:{dep_min+30 if dep_min < 30 else dep_min-30:02d}",
                        "lat": terminal["lat"],
                        "lng": terminal["lng"],
                        "address": terminal["name"],
                        "source": "BCFerries",
                        "attendees_count": random.randint(150, 400), # Passengers
                        "event_url": "https://www.bcferries.com/current-conditions"
                    })
        
        return events
