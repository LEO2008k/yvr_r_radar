import logging
import random
from datetime import datetime

logger = logging.getLogger(__name__)

class TrainsScraper:
    def scrape(self):
        logger.info("Generating static train schedule for today...")
        try:
            from datetime import timedelta
            try:
                from zoneinfo import ZoneInfo
                vancouver_tz = ZoneInfo("America/Vancouver")
            except ImportError:
                import pytz
                vancouver_tz = pytz.timezone("America/Vancouver")
            
            events_list = []
            
            # Generate for yesterday, today, tomorrow to avoid timezone boundary issues
            base_date = datetime.now(vancouver_tz).date()
            dates_to_generate = [base_date - timedelta(days=1), base_date, base_date + timedelta(days=1)]
            
            for d in dates_to_generate:
                date_str = d.strftime('%Y-%m-%d')
                
                # Pacific Central Station: lat 49.2736, lng -123.0978
                trains = [
                    {"title": "Amtrak Cascades 516 (Arrival from Seattle)", "time": f"{date_str} 11:45"},
                    {"title": "Amtrak Cascades 517 (Departure to Seattle)", "time": f"{date_str} 06:35"},
                    {"title": "Amtrak Cascades 518 (Arrival from Seattle)", "time": f"{date_str} 21:52"},
                    {"title": "Amtrak Cascades 519 (Departure to Seattle)", "time": f"{date_str} 17:45"},
                    {"title": "VIA Rail 'The Canadian' (Arrival from Toronto)", "time": f"{date_str} 08:00"},
                    {"title": "VIA Rail 'The Canadian' (Departure to Toronto)", "time": f"{date_str} 15:00"}
                ]
    
                for t in trains:
                    # Add a mock delay to some trains for UI demonstration
                    delay = random.choice([None, None, 15, 30, 45, 120])
                    
                    events_list.append({
                        "title": t['title'],
                        "source": "Train",
                        "time": t['time'],
                        "end_time": None,
                        "lat": 49.2736,
                        "lng": -123.0978,
                        "address": "Pacific Central Station, Vancouver",
                        "event_url": "https://www.amtrakcascades.com/",
                        "attendees_count": 0,
                        "is_online": False,
                        "delay_minutes": delay
                    })
            
            logger.info(f"Successfully generated {len(events_list)} trains across {len(dates_to_generate)} days.")
            return events_list
        except Exception as e:
            logger.error(f"Error generating trains: {e}")
            return []
