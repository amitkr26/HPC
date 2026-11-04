import os
import json
import sqlite3
from datetime import datetime

DB_NAME = "weather_data.db"

def setup_environment():
    print(f"Application Initialized. Current Working Directory: {os.getcwd()}")
    
    now = datetime.now()
    # Dynamically build path: ./archives/YYYY/MM/
    archive_path = os.path.join(".", "archives", now.strftime("%Y"), now.strftime("%m"))
    
    if not os.path.exists(archive_path):
        os.makedirs(archive_path)
        
    return archive_path

def cleanup_temp_cache():
    target = "temp_cache.txt"
    if os.path.exists(target):
        os.remove(target)
        print(f"Cleanup: {target} removed.")

def archive_raw_data(data_dict, archive_dir):
    filename = f"raw_weather_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(archive_dir, filename)
    
    with open(filepath, "w") as f:
        f.write(json.dumps(data_dict))

def init_db():
    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL
        )
    """)
    db.commit()
    db.close()

def insert_weather_data(temperature, timestamp):
    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()
    
    try:
        sql = "INSERT INTO weather_logs (timestamp, temperature) VALUES (?, ?)"
        cursor.execute(sql, (timestamp, temperature))
        db.commit()
    except sqlite3.Error as e:
        db.rollback()
        print(f"Database insertion failed: {e}")
        raise
    finally:
        db.close()

def get_all_weather():
    db = sqlite3.connect(DB_NAME)
    db.row_factory = sqlite3.Row  # Returns rows as dictionary-like objects
    cursor = db.cursor()
    cursor.execute("SELECT id, timestamp, temperature FROM weather_logs ORDER BY id DESC")
    rows = cursor.fetchall()
    db.close()
    return [dict(row) for row in rows]

if __name__ == '__main__':
    # Local testing isolation
    setup_environment()
    init_db()
    cleanup_temp_cache()