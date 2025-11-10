# backend/services/geocode_client.py

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# Initialize Nominatim geocoder (free, open source)
geolocator = Nominatim(user_agent="badminton_agent_app", timeout=10)

def geocode_address(address):
    """
    Convert an address string into latitude, longitude, and city name.
    Returns: (lat, lon, city) or (None, None, None) if not found
    """
    try:
        location = geolocator.geocode(address)
        if location:
            # Extract city from the address components
            address_parts = location.address.split(",")
            city = address_parts[-3].strip() if len(address_parts) >= 3 else ""
            return location.latitude, location.longitude, city
    except GeocoderTimedOut:
        # Retry once in case of timeout
        try:
            location = geolocator.geocode(address)
            if location:
                address_parts = location.address.split(",")
                city = address_parts[-3].strip() if len(address_parts) >= 3 else ""
                return location.latitude, location.longitude, city
        except Exception:
            pass
    return None, None, None


def reverse_geocode(lat, lon):
    """
    Convert latitude and longitude into a human-readable address.
    Returns: address string or None if not found
    """
    try:
        location = geolocator.reverse((lat, lon))
        if location:
            return location.address
    except GeocoderTimedOut:
        try:
            location = geolocator.reverse((lat, lon))
            if location:
                return location.address
        except Exception:
            pass
    return None
