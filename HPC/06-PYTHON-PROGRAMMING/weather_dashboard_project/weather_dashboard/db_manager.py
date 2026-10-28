import os
import sqlite3
from datetime import datetime

BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, "weather.db")
TEMP_CACHE = os.path.join(BASE_DIR, "temp_cache.txt")


def get_archive_dir():
    """Create (if needed) and return ./archives/<year>/<month>/ for today."""
    now = datetime.now()
    folder = os.path.join(BASE_DIR, "archives", str(now.year), f"{now.month:02d}")
    os.makedirs(folder, exist_ok=True)
    return folder


def remove_temp_cache():
    """Delete the old temp_cache.txt from the root folder if it is there."""
    if os.path.exists(TEMP_CACHE):
        os.remove(TEMP_CACHE)
        print("Old temp_cache.txt removed.")
        return True
    return False


def save_raw_json(raw_json):
    """Write the raw JSON string into a new .txt file in the archive folder."""
    remove_temp_cache()      # clean up before saving anything new

    folder = get_archive_dir()
    file_name = "weather_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
    file_path = os.path.join(folder, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(raw_json)

    return file_path


def init_db():
    """Create the weather_logs table if it does not exist yet."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS weather_logs (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   timestamp TEXT,
                   temperature REAL
               )"""
        )
        conn.commit()
    finally:
        conn.close()


def insert_weather_data(temp, time):
    """Insert one reading. Commits on success, rolls back on error."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        # parameterized query -> values are never pasted into the SQL text
        cursor.execute(
            "INSERT INTO weather_logs (timestamp, temperature) VALUES (?, ?)",
            (time, temp),
        )
        conn.commit()
        return True
    except sqlite3.Error as error:
        conn.rollback()
        print("Insert failed, rolled back:", error)
        raise
    finally:
        conn.close()


def get_all_weather():
    """Return every row of weather_logs as a list of dictionaries."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT id, timestamp, temperature FROM weather_logs ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


if __name__ == "__main__":
    # local test only - uses a throw-away database so the real one is untouched
    DB_PATH = os.path.join(BASE_DIR, "test_weather.db")
    init_db()
    insert_weather_data(12.5, "2026-10-23T15:00")
    print("Rows in test DB:", get_all_weather())
    os.remove(DB_PATH)
    print("Test database removed.")
