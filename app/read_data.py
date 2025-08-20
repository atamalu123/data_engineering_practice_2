import json
import pandas as pd
import os

"""
Builds paths relative to the script file for best practice
"""
def read_json(file_path: str) -> dict:
    request_data = {} # request data for same return
    try:
        base_dir = os.path.dirname(__file__) # get directory of file
        full_path = os.path.join(base_dir, file_path)
        with open(full_path, 'r') as file:
            request_data = json.load(file)
        return request_data
    except FileNotFoundError:
        print(f"Error: {full_path} was not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {full_path}")

def read_venues(file_path: str) -> pd.DataFrame:
    df = pd.DataFrame() # blank df for safe return
    try:
        base_dir = os.path.dirname(__file__) # get directory of file
        full_path = os.path.join(base_dir, file_path)
        df = pd.read_csv(full_path)
    except FileNotFoundError:
        print(f"Error: The file {full_path} was not found.")

    return df