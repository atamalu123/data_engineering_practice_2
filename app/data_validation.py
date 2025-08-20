"""
For validating inputs
"""

from datetime import datetime, date
import pandas as pd
import sqlite3

"""
Ensures string/date is in ISO format
"""
def is_datetime_valid(dt_str: str | date) -> bool:
    try:
        datetime.fromisoformat(dt_str)
    except:
        return False
    return True

"""
Ensures latitude is within valid range (-90 to 90)
"""
def is_latitude_valid(latitude: float) -> bool:
    if not (-90 <= latitude <= 90):
        raise ValueError(f"Latitude must be -90 <= lat <= 90. Latitude given: {latitude}")
    return True

"""
Ensures longitude is within valid range (-180 to 180)
"""
def is_longitude_valid(longitude: float) -> bool:
    if not (-180 <= longitude <= 180):
        raise ValueError(f"Longitude must be -180 <= long <= 180. Longitude given: {longitude}")
    return True

"""
Checks request:
  * Is venue id from request valid and in database/csv of venues?
  * Are dates valid ISO format?
  * Is end date >= start date?
"""
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
    # Make sure end_date is >= start_date
    start_date_dt = datetime.fromisoformat(start_date)
    end_date_dt = datetime.fromisoformat(end_date)
    if start_date_dt > end_date_dt:
        raise ValueError("Start date is later than end date.")

    return True

"""
Runs SQL QA checks:
  * Any duplicate rows?
  * Is temperature in range -90 to 60?
  * Is humidity in range 0 to 100?
"""
def run_qa_checks(db_path: str, table: str):
    checks = {
        "row_count": f"SELECT COUNT(*) FROM {table};",
        "duplicates": f"""
            SELECT COUNT(*) FROM (
                SELECT venue_id, ts_utc, COUNT(*) c
                FROM {table}
                GROUP BY venue_id, ts_utc
                HAVING c > 1
            );
        """,
        "temp_out_of_range": f"""
            SELECT COUNT(*) FROM {table}
            WHERE temperature_2m < -90 OR temperature_2m > 60;
        """,
        "humidity_out_of_range": f"""
            SELECT COUNT(*) FROM {table}
            WHERE relative_humidity_2m < 0 OR relative_humidity_2m > 100;
        """
    }

    results = {}
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        for name, sql in checks.items():
            cur.execute(sql)
            results[name] = cur.fetchone()[0]

    return results