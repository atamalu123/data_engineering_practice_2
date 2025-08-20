# Core tables

```
-- 1) Where is each venue?
-- Used venues.csv instead of SQL file for simplicity purposes
CREATE TABLE venues (
  venue_id   TEXT PRIMARY KEY,
  city       TEXT,
  lat        DOUBLE PRECISION NOT NULL,
  long       DOUBLE PRECISION NOT NULL,
);

-- 2) Hourly weather facts (wide row; one row per venue-hour)
--    Store in UTC; make (venue_id, ts_utc) the natural key for idempotent upserts.
CREATE TABLE weather_hourly (
  venue_id               TEXT NOT NULL,
  ts_utc                 TEXT NOT NULL,

  -- variables
  temperature_2m         REAL,
  relative_humidity_2m   REAL,
  dewpoint_2m            REAL,
  apparent_temperature   REAL,
  precipitation          REAL,
  rain                   REAL,
  snowfall               REAL,
  cloudcover             REAL,
  pressure_msl           REAL,
  surface_pressure       REAL,
  wind_speed_10m         REAL,
  wind_gusts_10m         REAL,

  PRIMARY KEY (venue_id, ts_utc),
  -- enforce hourly granularity
  CHECK (ts_utc = date_trunc('hour', ts_utc))
);

-- Helpful index for range queries per venue (the PK already helps)
CREATE INDEX weather_hourly_venue_ts_idx ON weather_hourly (venue_id, ts_utc);
```

# Upsert pattern

```
-- Example upsert for one row (your code will batch this)
INSERT INTO weather_hourly (
  venue_id, ts_utc, temperature_2m, relative_humidity_2m, dewpoint_2m,
  apparent_temperature, precipitation, rain, snowfall, cloudcover,
  pressure_msl, surface_pressure, wind_speed_10m, wind_gusts_10m, fetched_at
) VALUES (
  :venue_id, :ts_utc, :temperature_2m, :relative_humidity_2m, :dewpoint_2m,
  :apparent_temperature, :precipitation, :rain, :snowfall, :cloudcover,
  :pressure_msl, :surface_pressure, :wind_speed_10m, :wind_gusts_10m, now()
)
ON CONFLICT (venue_id, ts_utc) DO UPDATE SET
  temperature_2m       = EXCLUDED.temperature_2m,
  relative_humidity_2m = EXCLUDED.relative_humidity_2m,
  dewpoint_2m          = EXCLUDED.dewpoint_2m,
  apparent_temperature = EXCLUDED.apparent_temperature,
  precipitation        = EXCLUDED.precipitation,
  rain                 = EXCLUDED.rain,
  snowfall             = EXCLUDED.snowfall,
  cloudcover           = EXCLUDED.cloudcover,
  pressure_msl         = EXCLUDED.pressure_msl,
  surface_pressure     = EXCLUDED.surface_pressure,
  wind_speed_10m       = EXCLUDED.wind_speed_10m,
  wind_gusts_10m       = EXCLUDED.wind_gusts_10m,
  fetched_at           = now();
```