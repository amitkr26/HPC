import os
import json
import sqlite3
import logging

from flask import Flask, render_template, jsonify

from api_handler import fetch_weather, APIFetchError
from db_manager import init_db, save_raw_json, insert_weather_data, get_all_weather

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

app = Flask(__name__)
app.json.sort_keys = False      # keep fields in the order we build them (id first)

# startup: show where the script is running from and make sure the DB exists
current_path = os.getcwd()
print("Running from:", current_path)
logging.info("Application started from %s", current_path)
init_db()


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/api/v1/weather", methods=["GET"])
def get_weather():
    records = get_all_weather()
    return jsonify({"count": len(records), "records": records})


@app.route("/api/v1/update", methods=["POST"])
def update_weather():
    try:
        data = fetch_weather()
        current = data["current_weather"]

        save_raw_json(json.dumps(data, indent=2))
        insert_weather_data(current["temperature"], current["time"])

        logging.info("Weather updated: %s", current)
        return jsonify({"status": "success"}), 200

    except (APIFetchError, AssertionError, sqlite3.Error, OSError) as error:
        logging.error("Update failed: %s", error)
        return jsonify({"status": "error", "message": str(error)}), 500


if __name__ == "__main__":
    app.run(debug=False)
