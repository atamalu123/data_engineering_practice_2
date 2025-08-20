import openmeteo_requests
import requests_cache
from retry_requests import retry
import pandas as pd
from read_write_sql import generate_sql_table, copy_merge_weather_df, count_sql_table_rows
from data_validation import is_request_valid, is_latitude_valid, is_longitude_valid
from read_data import read_json, read_venues
# Optional: replace print() with logging.info()

##### 1. Ensure SQLite Database exists, if not, write one -----

### Read variables for fetch and write
WRITE_VARIABLES_DICT = read_json("../data/variables.json")
WRITE_VARIABLES = list(WRITE_VARIABLES_DICT.keys())
WRITE_VARIABLES_TYPES = list(WRITE_VARIABLES_DICT.values())

TABLE_NAME = "weather_hourly"

### Make new sql table if does not exist
generate_sql_table("weather.db", TABLE_NAME, WRITE_VARIABLES, WRITE_VARIABLES_TYPES)

##### 2. Process request and extract lat/long for processing -----

### Get request data (venue_id, start_date, end_date)
request_data = read_json("../data/request.json")

### Extract data from request
venue_id = request_data["venue_id"]
start_date = request_data["start_date"]
end_date = request_data["end_date"]

### Get lat/long from venues table
venues = read_venues("../data/venues.csv")

### Extract venue details
venue_id = request_data["venue_id"]
start_date = request_data["start_date"]
end_date = request_data["end_date"]

### Verify request data is valid
request_is_valid = is_request_valid(venue_id, start_date, end_date, venues)

### Get correct venue details
venue = venues[venues['venue_id'] == venue_id]

### Get latitude and longitude
latitude = venue['lat'].iloc[0]
longitude = venue['long'].iloc[0]

### Verify latitude and longitude are valid
latitude_is_valid = is_latitude_valid(latitude)
longitude_is_valid = is_longitude_valid(longitude)

CONFLICT_VARIABLES = ['venue_id', 'ts_utc']
HOURLY_VARIABLES = [key for key, value in WRITE_VARIABLES_DICT.items() if key not in CONFLICT_VARIABLES]

### Set up request for Open-Meteo API
params = {
    "latitude": latitude,
    "longitude": longitude,
    "hourly": HOURLY_VARIABLES,
    "start_date": start_date,
    "end_date": end_date
}

print(f"Successfully set up request to send to Open-Meteo: params = {params}")

##### 3. Get data from Open-Meteo API -----

### Setup the Open-Meteo API client with cache and retry on error
url = "https://archive-api.open-meteo.com/v1/archive"

cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

### Get response from Openmeteo API
try:
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]  # Process first location
except Exception as e:
    raise ConnectionError("Failed to get data from Open-Meteo API") from e

### Move response to dataframe
try:
    hourly = response.Hourly()

    # Build UTC timestamp column from start/end epoch seconds and the interval
    start_ts = pd.to_datetime(hourly.Time(), unit="s", utc=True)
    end_ts = pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True) 
    step = pd.Timedelta(seconds=hourly.Interval())

    df = pd.DataFrame({
        "venue_id": venue_id,
        "ts_utc": pd.date_range(start=start_ts, end=end_ts, freq=step, inclusive="left")
    })

    # Add date/hour columns
    df["date_utc"] = df["ts_utc"].dt.date
    df["hour_utc"] = df["ts_utc"].dt.hour

    # Add variables from response to dataframe
    for i, name in enumerate(HOURLY_VARIABLES):
        df[name] = hourly.Variables(i).ValuesAsNumpy()
except Exception as e:
    raise ValueError("Failed to move data from response to dataframe.") from e

print("Successfully retrieved data from Open-Meteo.")

##### 4. Export to SQL -----

### Determine number of rows before write
num_rows_before = count_sql_table_rows("../data/weather.db", TABLE_NAME)
print(f"Number of rows before adding to {TABLE_NAME}: {num_rows_before}")

### Determine number of rows affected by merge
num_rows_written = copy_merge_weather_df(df, WRITE_VARIABLES, venue_id, CONFLICT_VARIABLES, TABLE_NAME, "data/weather.db")
num_rows_after = count_sql_table_rows("../data/weather.db", TABLE_NAME)

if num_rows_after > num_rows_before:
    print(f"Successfully wrote {num_rows_written} rows to {TABLE_NAME}")
else:
    print(f"Did not write additional rows to {TABLE_NAME}")