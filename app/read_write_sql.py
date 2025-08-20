import io
import pandas as pd
import psycopg2
import os
import json
import sqlite3

### For reading 
# file_path = weather.db
def generate_sql_table(file_path: str, table_name: str, col_names: str, col_types: str):

    ### Construct file paths
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) # Project base dir = parent of /app
    DB_PATH = os.path.join(BASE_DIR, file_path)

    if os.path.isabs(file_path):
        DB_PATH = file_path
    else:
        rel = file_path.replace("\\", "/")
        if rel.startswith("data/"):
            DB_PATH = os.path.join(BASE_DIR, rel)
        else:
            DB_PATH = os.path.join(BASE_DIR, "data", rel)
    DB_PATH = os.path.normpath(DB_PATH)

    ### Build column DDL
    ddl_cols = []
    for i in range(len(col_names)):
        not_null = " NOT NULL" if col_names[i] in ("venue_id", "ts_utc") else ""
        ddl_cols.append(f'    "{col_names[i]}" {col_types[i]}{not_null}')

    ### From column DDL, build script to execute
    ddl = (
        f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
        + ",\n".join(ddl_cols)
        + ",\n    fetched_at TEXT DEFAULT (CURRENT_TIMESTAMP),\n"
        + '    PRIMARY KEY ("venue_id","ts_utc")\n'
        + ");"
    )

    ### Write to local
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(ddl)
            conn.commit()
    except:
        raise ConnectionError(f"Could not write to {DB_PATH}")
    
    print(f"Generated file using schema: {ddl}")

def construct_staging_table_string(stage_table: str, col_names: list[str], col_types: list[str]) -> str:
        execute_string_start = f"CREATE TEMP TABLE {stage_table} ("
        execute_string_body = ""
        for i in range(len(col_names)):
            execute_string_body += f"{col_names[i]} "
            if i != len(col_names)-1: # comma unless last col
                execute_string_body += f"{col_types[i]},"
            else:
                execute_string_body += f"{col_types[i]}"
        execute_string_end = ") ON COMMIT DROP;"

        execute_string = execute_string_start + execute_string_body + execute_string_end

        return execute_string

def construct_merge_table_string(table_name: str, stage_table: str, col_names: list[str], conflict_variables: list[str]) -> str:
    update_col_names = [c for c in col_names if c not in conflict_variables]

    execute_string_insert = f"INSERT INTO {table_name} ({', '.join(col_names)}) "
    execute_string_select = f"SELECT {', '.join(col_names)} FROM {stage_table} "
    execute_string_conflict_start = f"ON CONFLICT ({', '.join(conflict_variables)}) DO UPDATE SET "
    execute_string_conflict_body = ""
    for col_name in update_col_names:
        execute_string_conflict_body += f"{col_name} = EXCLUDED.{col_name}, "
    execute_string_conflict_end = "fetched_at = now();"

    execute_string = execute_string_insert + execute_string_select + execute_string_conflict_start + execute_string_conflict_body + execute_string_conflict_end

    return execute_string

"""
Upsert df into a local SQLite file.
    - If dsn_or_path ends with .db or has no scheme, it's treated as a SQLite file path.
    - Expects a composite PRIMARY KEY (venue_id, ts_utc) in the target table.
"""

def copy_merge_weather_df(df: pd.DataFrame, col_names: list[str], venue_id: str, conflict_variables: list[str], table_name: str, dsn_or_path: str) -> int:
    ### Resolve DB path relative to /app if a relative path is provided
    if not os.path.isabs(dsn_or_path):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        db_path = os.path.join(base_dir, dsn_or_path)
    else:
        db_path = dsn_or_path

    ### Prepare dataframe to match columns and types
    df2 = df.copy()
    df2["venue_id"] = venue_id
    # Normalize ts_utc to ISO8601 Z (TEXT) to match SQLite schema
    df2["ts_utc"] = pd.to_datetime(df2["ts_utc"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    ### Ensure column order and NULLs as Python None
    df2 = df2[col_names]
    df2 = df2.where(pd.notnull(df2), None)

    ### Build UPSERT SQL for SQLite
    update_cols = [c for c in col_names if c not in conflict_variables]
    placeholders = ",".join("?" for _ in col_names)
    insert_cols = ",".join(f'"{c}"' for c in col_names)
    conflict_cols = ",".join(f'"{c}"' for c in conflict_variables)
    set_clause = ", ".join(f'"{c}"=excluded."{c}"' for c in update_cols)
    sql = (
        f'INSERT INTO "{table_name}" ({insert_cols}) VALUES ({placeholders}) '
        f'ON CONFLICT ({conflict_cols}) DO UPDATE SET {set_clause}, '
        f'fetched_at=CURRENT_TIMESTAMP;'
    )

    ### Execute in a transaction
    tuples = [tuple(row) for row in df2.itertuples(index=False, name=None)]
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.executemany(sql, tuples)
        affected = cur.rowcount  # may be -1 in sqlite for executemany; fallback below
        conn.commit()

    ### Fallback count if sqlite returns -1
    return len(tuples) if (affected is None or affected < 0) else affected

def count_sql_table_rows(file_path: str, table_name: str) -> int:
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), file_path))

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        # Replace 'weather_hourly' with your actual table name
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cur.fetchone()[0]

    return count