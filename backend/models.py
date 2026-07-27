from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base
import datetime

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    time = Column(DateTime)
    lat = Column(Float)
    lng = Column(Float)
    address = Column(String)
    source = Column(String)
    end_time = Column(DateTime, nullable=True)
    attendees_count = Column(Integer, default=0)
    event_url = Column(String, nullable=True)
    delay_minutes = Column(Integer, nullable=True)

class ScraperStatus(Base):
    __tablename__ = "scraper_status"

    id = Column(Integer, primary_key=True, index=True)
    scraper_name = Column(String, index=True)
    last_run = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String) # "SUCCESS" or "ERROR"
    events_found = Column(Integer, default=0)
    error_message = Column(String, nullable=True)

class ScrapeLog(Base):
    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    total_found = Column(Integer, default=0)
    online_filtered = Column(Integer, default=0)
    saved_to_db = Column(Integer, default=0)

class ApiStatus(Base):
    __tablename__ = "api_status"

    api_name = Column(String, primary_key=True, index=True)
    is_healthy = Column(Integer, default=1)
    last_checked = Column(DateTime, default=datetime.datetime.utcnow)
    last_status_change = Column(DateTime, default=datetime.datetime.utcnow)
    error_message = Column(String, nullable=True)

class LocationHistory(Base):
    __tablename__ = "location_history"

    id = Column(Integer, primary_key=True, index=True)
    lat = Column(Float)
    lng = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
