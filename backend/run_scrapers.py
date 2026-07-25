import os
import asyncio
from scrapers import LumaScraper, MeetupScraper, AllEventsScraper
from database import SessionLocal, engine
from models import Event, Base
from datetime import datetime, timedelta

# Initialize tables
Base.metadata.create_all(bind=engine)

def scrape_all():
    print("Starting scrapers...")
    scrapers = [
        LumaScraper(),
        MeetupScraper(),
        AllEventsScraper()
    ]
    
    all_events = []
    
    for scraper in scrapers:
        print(f"Running {scraper.__class__.__name__}...")
        events = scraper.scrape()
        all_events.extend(events)
        print(f"Got {len(events)} events from {scraper.__class__.__name__}")
        
    print(f"Total events scraped: {len(all_events)}")
    
    print("Events:")
    for ev in all_events:
        print(f"- {ev['title']} at {ev['time']} [{ev['source']}]")
        
    db = SessionLocal()
    try:
        from models import ScrapeLog
        
        total_found = len(all_events)
        filtered_events = [ev for ev in all_events if not ev.get('is_online', False)]
        online_filtered = total_found - len(filtered_events)
        
        one_month_ago = datetime.now() - timedelta(days=30)
        deleted_count = db.query(Event).filter(Event.time < one_month_ago).delete()
        print(f"Deleted {deleted_count} events older than 30 days.")
        
        saved_count = 0
        for ev in filtered_events:
            # Parse datetime string
            dt_obj = datetime.strptime(ev['time'], "%Y-%m-%d %H:%M")
            end_dt_obj = datetime.strptime(ev['end_time'], "%Y-%m-%d %H:%M") if ev.get('end_time') else None
            
            # Check if event exists (simple deduplication by title and time)
            existing = db.query(Event).filter(Event.title == ev['title'], Event.time == dt_obj).first()
            if not existing:
                new_event = Event(
                    title=ev['title'],
                    time=dt_obj,
                    end_time=end_dt_obj,
                    lat=ev['lat'],
                    lng=ev['lng'],
                    address=ev['address'],
                    source=ev['source'],
                    attendees_count=ev.get('attendees_count', 0),
                    event_url=ev.get('event_url')
                )
                db.add(new_event)
                saved_count += 1
                
        # Record stats
        log_entry = ScrapeLog(
            total_found=total_found,
            online_filtered=online_filtered,
            saved_to_db=saved_count
        )
        db.add(log_entry)
        
        db.commit()
        print(f"Events saved to database: {saved_count} new events.")
    except Exception as e:
        print(f"Error saving to db: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    scrape_all()
