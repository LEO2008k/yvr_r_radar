import os
import httpx
import urllib.parse
from typing import Tuple, Optional

# Simple cache to avoid redundant API calls for the same address during a scraping run
_GEOCODE_CACHE = {}

def get_lat_lng(address: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Uses Google Maps Geocoding API to resolve a text address into lat, lng.
    Falls back to a default location (Vancouver center) if geocoding fails.
    """
    api_key = os.getenv("GEOCODING_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("Geocoding failed: No valid GEOCODING_API_KEY found.")
        return None, None
        
    if not address or not address.strip():
        return None, None
        
    # Append 'BC, Canada' to help the geocoder if it's just a venue name
    search_address = f"{address.strip()}, BC, Canada"
    
    if search_address in _GEOCODE_CACHE:
        return _GEOCODE_CACHE[search_address]
        
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(search_address)}&key={api_key}"
    
    try:
        # Using a synchronous client for simplicity in the scraper pipeline
        with httpx.Client() as client:
            response = client.get(url, timeout=10.0)
            data = response.json()
            
            if data.get("status") == "OK" and len(data.get("results", [])) > 0:
                location = data["results"][0]["geometry"]["location"]
                lat = location.get("lat")
                lng = location.get("lng")
                _GEOCODE_CACHE[search_address] = (lat, lng)
                return lat, lng
            else:
                print(f"Geocoding returned non-OK status for '{search_address}': {data.get('status')}")
    except Exception as e:
        print(f"Error during geocoding '{search_address}': {e}")
        
    _GEOCODE_CACHE[search_address] = (None, None)
    return None, None
