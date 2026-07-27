from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import httpx
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime, date, time, timedelta
from database import SessionLocal, engine
from models import Event, ScrapeLog, ApiStatus, ScraperStatus, LocationHistory, Base
from starlette.middleware.sessions import SessionMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from run_scrapers import scrape_all
from contextlib import asynccontextmanager
import urllib.parse
import math
import urllib.parse
from pydantic import BaseModel
from typing import Optional

class MobileLocation(BaseModel):
    lat: float
    lng: float
    device_type: Optional[str] = "mobile"

latest_mobile_location = {
    "lat": None,
    "lng": None,
    "updated_at": None,
    "device_type": "mobile"
}

def check_api_health():
    db = SessionLocal()
    try:
        checks = {
            "Google Geocoding": {"url": None, "type": "google"},
            "Luma": {"url": "https://lu.ma/vancouver", "type": "http"},
            "Meetup": {"url": "https://www.meetup.com/find/?location=ca--bc--Vancouver&source=EVENTS", "type": "http"},
            "AllEvents": {"url": "https://allevents.in/vancouver/all", "type": "http"}
        }
        
        for name, info in checks.items():
            is_healthy = 1
            error_msg = None
            
            try:
                if info["type"] == "google":
                    api_key = os.getenv("GEOCODING_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")
                    if not api_key or api_key == "YOUR_API_KEY_HERE":
                        raise Exception("Missing GEOCODING_API_KEY")
                    search_address = "Vancouver, BC, Canada"
                    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(search_address)}&key={api_key}"
                    with httpx.Client() as client:
                        resp = client.get(url, timeout=10.0)
                        data = resp.json()
                        if data.get("status") != "OK":
                            raise Exception(f"Google API Error: {data.get('status')} - {data.get('error_message', '')}")
                else:
                    headers = {"User-Agent": "Mozilla/5.0"}
                    with httpx.Client(headers=headers, follow_redirects=True) as client:
                        resp = client.get(info["url"], timeout=15.0)
                        resp.raise_for_status()
            except Exception as e:
                is_healthy = 0
                error_msg = str(e)
                
            # Update DB
            status_record = db.query(ApiStatus).filter(ApiStatus.api_name == name).first()
            now = datetime.utcnow()
            if status_record:
                if status_record.is_healthy != is_healthy:
                    status_record.last_status_change = now
                status_record.is_healthy = is_healthy
                status_record.last_checked = now
                status_record.error_message = error_msg
            else:
                new_status = ApiStatus(
                    api_name=name,
                    is_healthy=is_healthy,
                    last_checked=now,
                    last_status_change=now,
                    error_message=error_msg
                )
                db.add(new_status)
        db.commit()
    except Exception as e:
        print(f"Health check failed: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the scheduler when app starts
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_all, 'interval', hours=12)
    scheduler.add_job(check_api_health, 'interval', minutes=15)
    scheduler.start()
    
    # Run once at startup as well
    scrape_all()
    check_api_health()
    
    yield
    # Shutdown the scheduler when app stops
    scheduler.shutdown()

# Ensure all tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(title="YVR Radar", version="1.0.0", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "super-secret-key"))
templates = Jinja2Templates(directory="templates")

failed_attempts = {}

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
CAPTCHA_SECRET = os.getenv("CAPTCHA_SECRET", "")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "YOUR_API_KEY_HERE")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    if not request.session.get("authenticated"):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"GOOGLE_MAPS_API_KEY": GOOGLE_MAPS_API_KEY}
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Login - YVR Radar</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
    </head>
    <body class="bg-gray-900 text-white flex items-center justify-center h-screen">
        <form method="post" action="/login" class="bg-gray-800 p-8 rounded-lg shadow-lg w-96">
            <h2 class="text-2xl font-bold mb-6 text-center text-emerald-400">Secure Login</h2>
            <div class="mb-4">
                <label class="block text-gray-400 mb-2">Username</label>
                <input type="text" name="username" class="w-full p-2 rounded bg-gray-700 border border-gray-600 focus:border-emerald-500 outline-none text-white">
            </div>
            <div class="mb-6">
                <label class="block text-gray-400 mb-2">Password</label>
                <input type="password" name="password" class="w-full p-2 rounded bg-gray-700 border border-gray-600 focus:border-emerald-500 outline-none text-white">
            </div>
            <div class="cf-turnstile mb-6" data-sitekey="1x00000000000000000000AA"></div>
            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-2 px-4 rounded">Sign In</button>
        </form>
    </body>
    </html>
    """

@app.post("/login")
async def do_login(request: Request, username: str = Form(...), password: str = Form(...), cf_turnstile_response: str = Form(None)):
    client_ip = request.client.host
    if failed_attempts.get(client_ip, 0) >= 12:
        raise HTTPException(status_code=403, detail="Too many failed attempts. Your IP is blocked.")
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        failed_attempts[client_ip] = 0
        request.session["authenticated"] = True
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    else:
        failed_attempts[client_ip] = failed_attempts.get(client_ip, 0) + 1
        raise HTTPException(status_code=401, detail="Invalid credentials")

def require_auth(request: Request):
    if not request.session.get("authenticated"):
        raise HTTPException(status_code=401, detail="Not authenticated")

@app.get("/api/events", dependencies=[Depends(require_auth)])
async def get_events():
    db = SessionLocal()
    try:
        # Get all events (the database automatically prunes events older than 30 days)
        events = db.query(Event).all()
        
        results = []
        for ev in events:
            # Return full ISO format string so frontend can parse dates
            time_str = ev.time.isoformat()
            end_time_str = ev.end_time.isoformat() if ev.end_time else None
            results.append({
                "id": ev.id,
                "title": ev.title,
                "time": time_str,
                "end_time": end_time_str,
                "lat": ev.lat,
                "lng": ev.lng,
                "address": ev.address,
                "source": ev.source,
                "attendees_count": ev.attendees_count,
                "event_url": ev.event_url,
                "delay_minutes": ev.delay_minutes
            })
        return JSONResponse(content=results)
    finally:
        db.close()

@app.post("/api/location", dependencies=[Depends(require_auth)])
async def update_location(loc: MobileLocation):
    # Update global state for quick latest poll
    latest_mobile_location["lat"] = loc.lat
    latest_mobile_location["lng"] = loc.lng
    latest_mobile_location["device_type"] = loc.device_type
    now = datetime.now()
    latest_mobile_location["updated_at"] = now.isoformat()
    
    # Save to database history
    db = SessionLocal()
    try:
        new_loc = LocationHistory(
            lat=loc.lat,
            lng=loc.lng,
            timestamp=now
        )
        db.add(new_loc)
        
        # Prune history older than 1 year to keep DB manageable
        cutoff = now - timedelta(days=365)
        db.query(LocationHistory).filter(LocationHistory.timestamp < cutoff).delete()
        db.commit()
    finally:
        db.close()
        
    return {"status": "ok"}

@app.get("/api/location", dependencies=[Depends(require_auth)])
async def get_location():
    return JSONResponse(content=latest_mobile_location)

@app.get("/api/location/history", dependencies=[Depends(require_auth)])
async def get_location_history(range_type: str = "day", snap: bool = False):
    db = SessionLocal()
    try:
        now = datetime.now()
        if range_type == "week":
            cutoff = now - timedelta(days=7)
        elif range_type == "month":
            cutoff = now - timedelta(days=30)
        elif range_type == "year":
            cutoff = now - timedelta(days=365)
        else: # default to day
            cutoff = now - timedelta(hours=24)
            
        history = db.query(LocationHistory).filter(
            LocationHistory.timestamp >= cutoff
        ).order_by(LocationHistory.timestamp.asc()).all()
        
        results = [
            {
                "lat": h.lat,
                "lng": h.lng,
                "timestamp": h.timestamp.isoformat()
            }
            for h in history
        ]

        if snap and GOOGLE_MAPS_API_KEY and GOOGLE_MAPS_API_KEY != "YOUR_API_KEY_HERE":
            def haversine(lat1, lon1, lat2, lon2):
                R = 6371000
                phi1, phi2 = math.radians(lat1), math.radians(lat2)
                dphi = math.radians(lat2 - lat1)
                dlambda = math.radians(lon2 - lon1)
                a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
                return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

            filtered = []
            last_pt = None
            for pt in results:
                if not last_pt:
                    filtered.append(pt)
                    last_pt = pt
                else:
                    dist = haversine(last_pt["lat"], last_pt["lng"], pt["lat"], pt["lng"])
                    if dist > 50:
                        filtered.append(pt)
                        last_pt = pt
            
            # Google Roads API allows max 100 points per request
            snapped_results = []
            chunk_size = 100
            
            async with httpx.AsyncClient() as client:
                for i in range(0, len(filtered), chunk_size):
                    chunk = filtered[i:i+chunk_size]
                    path_str = "|".join([f"{pt['lat']},{pt['lng']}" for pt in chunk])
                    
                    url = f"https://roads.googleapis.com/v1/snapToRoads?path={path_str}&interpolate=true&key={GOOGLE_MAPS_API_KEY}"
                    try:
                        resp = await client.get(url, timeout=10.0)
                        if resp.status_code == 200:
                            data = resp.json()
                            if "snappedPoints" in data:
                                for sp in data["snappedPoints"]:
                                    loc = sp["location"]
                                    orig_idx = sp.get("originalIndex")
                                    # If it's an interpolated point, we don't have an exact timestamp
                                    ts = chunk[orig_idx]["timestamp"] if orig_idx is not None and orig_idx < len(chunk) else None
                                    snapped_results.append({
                                        "lat": loc["latitude"],
                                        "lng": loc["longitude"],
                                        "timestamp": ts
                                    })
                    except Exception as e:
                        print("Error snapping to roads:", e)
                        
            # If snapping worked and returned points, use them
            if snapped_results:
                results = snapped_results

        return JSONResponse(content=results)
    finally:
        db.close()

@app.get("/stats", response_class=HTMLResponse)
async def read_stats(request: Request):
    if not request.session.get("authenticated"):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    return templates.TemplateResponse(
        request=request, 
        name="stats.html", 
        context={}
    )

@app.get("/api/stats", dependencies=[Depends(require_auth)])
async def get_stats():
    db = SessionLocal()
    try:
        logs = db.query(ScrapeLog).order_by(ScrapeLog.timestamp.desc()).limit(10).all()
        
        # Today's events count
        today = date.today()
        start_of_day = datetime.combine(today, time.min)
        end_of_day = datetime.combine(today, time.max)
        events_today = db.query(Event).filter(Event.time >= start_of_day, Event.time <= end_of_day).count()

        return JSONResponse(content={
            "events_today": events_today,
            "logs": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "total_found": log.total_found,
                    "online_filtered": log.online_filtered,
                    "saved_to_db": log.saved_to_db
                }
                for log in logs
            ]
        })
    finally:
        db.close()

@app.get("/status", response_class=HTMLResponse)
async def read_status(request: Request):
    if not request.session.get("authenticated"):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        
    db = SessionLocal()
    try:
        scraper_statuses = db.query(ScraperStatus).order_by(ScraperStatus.scraper_name, ScraperStatus.last_run.desc()).all()
        # Get latest for each scraper
        latest_statuses = {}
        for st in scraper_statuses:
            if st.scraper_name not in latest_statuses:
                latest_statuses[st.scraper_name] = st
                
        return templates.TemplateResponse(
            request=request, 
            name="status.html", 
            context={
                "scraper_statuses": list(latest_statuses.values())
            }
        )
    finally:
        db.close()

@app.get("/api/status", dependencies=[Depends(require_auth)])
async def get_status():
    db = SessionLocal()
    try:
        # DB check (if we get here, DB connection works)
        db_status = True
        
        # Last Cron job check
        last_log = db.query(ScrapeLog).order_by(ScrapeLog.timestamp.desc()).first()
        last_sync_time = last_log.timestamp.isoformat() if last_log else None
        
        cron_status = False
        import datetime as dt
        if last_log:
            time_diff = dt.datetime.utcnow() - last_log.timestamp
            cron_status = time_diff.total_seconds() < 86400 # 24 hours
            
        # Get all API statuses
        apis = db.query(ApiStatus).all()
        api_list = []
        for api in apis:
            api_list.append({
                "api_name": api.api_name,
                "is_healthy": bool(api.is_healthy),
                "last_checked": api.last_checked.isoformat() if api.last_checked else None,
                "last_status_change": api.last_status_change.isoformat() if api.last_status_change else None,
                "error_message": api.error_message
            })
            
        scraper_statuses = db.query(ScraperStatus).order_by(ScraperStatus.scraper_name, ScraperStatus.last_run.desc()).all()
        latest_statuses = {}
        for st in scraper_statuses:
            if st.scraper_name not in latest_statuses:
                latest_statuses[st.scraper_name] = {
                    "scraper_name": st.scraper_name,
                    "status": st.status,
                    "last_run": st.last_run.isoformat() if st.last_run else None,
                    "events_found": st.events_found,
                    "error_message": st.error_message
                }
            
        return JSONResponse(content={
            "db_status": db_status,
            "cron_status": cron_status,
            "last_sync_time": last_sync_time,
            "api_statuses": api_list,
            "scraper_statuses": list(latest_statuses.values())
        })
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    finally:
        db.close()

@app.post("/api/scrape/luma")
async def scrape_luma():
    url = "https://lu.ma/vancouver"
    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
        try:
            response = await client.get(url, follow_redirects=True)
            soup = BeautifulSoup(response.text, 'html.parser')
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data:
                data = json.loads(next_data.string)
                return {"status": "success", "message": "Parsed Next.js data", "bytes_length": len(next_data.string)}
            else:
                return {"status": "warning", "message": "Could not find __NEXT_DATA__ script tag on lu.ma"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

@app.post("/api/scrape/ferries")
async def scrape_ferries():
    from scrapers.bcferries import BCFerriesScraper
    db = SessionLocal()
    scraper_name = "BCFerriesScraper"
    try:
        scraper = BCFerriesScraper()
        ferry_events = scraper.scrape()
        
        # Delete existing ferry events for the future to avoid duplicates
        # Actually, let's just delete all BCFerries events and replace them, since it generates current data
        db.query(Event).filter(Event.source == "BCFerries").delete()
        
        saved_count = 0
        for ev in ferry_events:
            time_dt = datetime.strptime(ev["time"], "%Y-%m-%d %H:%M")
            end_time_dt = datetime.strptime(ev["end_time"], "%Y-%m-%d %H:%M") if ev.get("end_time") else None
            
            db_event = Event(
                title=ev["title"],
                time=time_dt,
                end_time=end_time_dt,
                lat=ev["lat"],
                lng=ev["lng"],
                address=ev["address"],
                source=ev["source"],
                attendees_count=ev.get("attendees_count", 0),
                event_url=ev.get("event_url", "")
            )
            db.add(db_event)
            saved_count += 1
            
        status_entry = ScraperStatus(
            scraper_name=scraper_name,
            status="SUCCESS",
            events_found=saved_count,
            error_message=None
        )
        db.add(status_entry)
        db.commit()
        return {"status": "success", "message": f"Scraped and saved {saved_count} ferry events."}
    except Exception as e:
        db.rollback()
        status_entry = ScraperStatus(
            scraper_name=scraper_name,
            status="ERROR",
            events_found=0,
            error_message=str(e)
        )
        db.add(status_entry)
        db.commit()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@app.post("/api/scrape/trains")
async def scrape_trains():
    from scrapers.trains import TrainsScraper
    db = SessionLocal()
    scraper_name = "TrainsScraper"
    try:
        scraper = TrainsScraper()
        train_events = scraper.scrape()
        
        db.query(Event).filter(Event.source == "Train").delete()
        
        saved_count = 0
        for ev in train_events:
            time_dt = datetime.strptime(ev["time"], "%Y-%m-%d %H:%M")
            end_time_dt = datetime.strptime(ev["end_time"], "%Y-%m-%d %H:%M") if ev.get("end_time") else None
            
            db_event = Event(
                title=ev["title"],
                time=time_dt,
                end_time=end_time_dt,
                lat=ev["lat"],
                lng=ev["lng"],
                address=ev["address"],
                source=ev["source"],
                attendees_count=ev.get("attendees_count", 0),
                event_url=ev.get("event_url", ""),
                delay_minutes=ev.get("delay_minutes", 0)
            )
            db.add(db_event)
            saved_count += 1
            
        status_entry = ScraperStatus(
            scraper_name=scraper_name,
            status="SUCCESS",
            events_found=saved_count,
            error_message=None
        )
        db.add(status_entry)
        db.commit()
        return {"status": "success", "message": f"Scraped and saved {saved_count} train events."}
    except Exception as e:
        db.rollback()
        status_entry = ScraperStatus(
            scraper_name=scraper_name,
            status="ERROR",
            events_found=0,
            error_message=str(e)
        )
        db.add(status_entry)
        db.commit()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@app.post("/api/scrape/afterparties")
async def scrape_afterparties():
    from scrapers.afterparties import AfterpartiesScraper
    db = SessionLocal()
    scraper_name = "AfterpartiesScraper"
    try:
        scraper = AfterpartiesScraper()
        events = scraper.scrape()
        
        db.query(Event).filter(Event.source == "Afterparty").delete()
        
        saved_count = 0
        for ev in events:
            time_dt = datetime.strptime(ev["time"], "%Y-%m-%d %H:%M")
            end_time_dt = datetime.strptime(ev["end_time"], "%Y-%m-%d %H:%M") if ev.get("end_time") else None
            
            db_event = Event(
                title=ev["title"],
                time=time_dt,
                end_time=end_time_dt,
                lat=ev["lat"],
                lng=ev["lng"],
                address=ev["address"],
                source=ev["source"],
                attendees_count=ev.get("attendees_count", 0),
                event_url=ev.get("event_url", "")
            )
            db.add(db_event)
            saved_count += 1
            
        status_entry = ScraperStatus(
            scraper_name=scraper_name,
            status="SUCCESS",
            events_found=saved_count,
            error_message=None
        )
        db.add(status_entry)
        db.commit()
        return {"status": "success", "message": f"Scraped and saved {saved_count} afterparty events."}
    except Exception as e:
        db.rollback()
        status_entry = ScraperStatus(
            scraper_name=scraper_name,
            status="ERROR",
            events_found=0,
            error_message=str(e)
        )
        db.add(status_entry)
        db.commit()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
