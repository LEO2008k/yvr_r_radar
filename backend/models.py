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

class ScrapeLog(Base):
    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    total_found = Column(Integer, default=0)
    online_filtered = Column(Integer, default=0)
    saved_to_db = Column(Integer, default=0)
