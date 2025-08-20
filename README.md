# API Pipeline Take-home

Adapted from [here](https://www.reddit.com/r/dataengineering/comments/1jy09o8/is_this_takehome_assignment_too_large_and_complex/).

No setup required, just download and run `main.py`. For testing, try deleting different files in `/data/` or adding to `variables.json`.

# Assignment Summary

Build a Python data pipeline and expose it via an API.

The API must:
  * Accept a venue ID, start date, and end date.
  * Use Open-Meteo's historical weather API to fetch hourly weather data for the specified range and location.
  * Extract 10+ parameters (e.g., temperature, precipitation, snowfall, etc.).
  * Store the data in a cloud-hosted database.
  * Return success or error responses accordingly.

* Design the database schema for storing the weather data.
* Use OpenAPI 3.0 to document the API.
* Deploy locally
* ~~Set up CI/CD pipeline for the solution.~~ not done yet
* Include a README with setup instructions (current file)
* ~~Implement QA checks in SQL for data consistency.~~ not done yet

# Files

## Python files

  * `data_validation` - used to validate inputs
  * `main.py` - used to retrieve data from OpenMeteo API and store in local SQLite file
  * `read_data.py` - used to read data and handle when data is missing
  * `read_write_sql.py` - used for generation of SQLite file (`weather.db`) if none exists and for writing to database

## Data files
  
  * `request.json` - used to simulate accepting `venue_id`, `start_date`, and `end_date`
  * `variables.json` - variables to write to database, in addition to getting from OpenMeteo's API
  * `venues.csv` - used to simulate SQL table holding information of all venues
  * `weather.db` - SQLite server to get data from 

