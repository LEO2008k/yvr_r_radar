import os
import asyncio
from scrapers import LumaScraper, MeetupScraper, AllEventsScraper, TrainsScraper
from database import SessionLocal, engine
from models import Event, Base, ScraperStatus
from datetime import datetime, timedelta

# Initialize tables
Base.metadata.create_all(bind=engine)

def scrape_all():
    print("Starting scrapers...")
    scrapers = [
        # LumaScraper(), # Disabled: This scraper currently generates mock/fake data

        MeetupScraper(),
        AllEventsScraper(),
        TrainsScraper()
    ]
    
    all_events = []
    
    db = SessionLocal()
    for scraper in scrapers:
        scraper_name = scraper.__class__.__name__
        print(f"Running {scraper_name}...")
        try:
            events = scraper.scrape()
            all_events.extend(events)
            
            # Log success
            status_entry = ScraperStatus(
                scraper_name=scraper_name,
                status="SUCCESS",
                events_found=len(events),
                error_message=None
            )
            db.add(status_entry)
            print(f"Got {len(events)} events from {scraper_name}")
        except Exception as e:
            # Log error
            status_entry = ScraperStatus(
                scraper_name=scraper_name,
                status="ERROR",
                events_found=0,
                error_message=str(e)
            )
            db.add(status_entry)
            print(f"Error running {scraper_name}: {e}")
            
    db.commit()
        
    print(f"Total events scraped: {len(all_events)}")
    
    print("Events:")
    for ev in all_events:
        print(f"- {ev['title']} at {ev['time']} [{ev['source']}]")
        
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
                    event_url=ev.get('event_url'),
                    delay_minutes=ev.get('delay_minutes')
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
