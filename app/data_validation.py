"""
For validating inputs
"""

from datetime import datetime, date
import pandas as pd

def is_datetime_valid(dt_str: str | date) -> bool:
    try:
        datetime.fromisoformat(dt_str)
    except:
        return False
    return True

def is_latitude_valid(latitude: float) -> bool:
    if not (-90 <= latitude <= 90):
        raise ValueError(f"Latitude must be -90 <= lat <= 90. Latitude given: {latitude}")
    return True
    
def is_longitude_valid(longitude: float) -> bool:
    if not (-180 <= longitude <= 180):
        raise ValueError(f"Longitude must be -180 <= long <= 180. Longitude given: {longitude}")
    return True

def is_request_valid(venue_id: str, start_date: str | date, end_date: str | date, venues_df: pd.DataFrame) -> bool:
    # Subset data
    try:
        sub_df = venues_df[venues_df["venue_id"] == venue_id]
    except:
        raise ValueError("Unable to subset data.")
    # Ensure venue id is in dataframe and only occurs once
    if len(sub_df) < 1:
        raise ValueError(f"Venue {venue_id} not found.")
    if len(sub_df) > 1:
        raise ValueError(f"More than 1 entry for venue_id = {venue_id} detected.")
    # Check dates
    is_datetime_valid(start_date)
    is_datetime_valid(end_date)

    return True