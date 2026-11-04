from flask import Flask, render_template, jsonify
from api_handler import fetch_weather_data, APIFetchError
from db_manager import (
    setup_environment, 
    cleanup_temp_cache, 
    archive_raw_data, 
    init_db, 
    insert_weather_data, 
    get_all_weather
)

app = Flask(__name__)

# Initialize system requirements on boot
ARCHIVE_DIR = setup_environment()
init_db()
cleanup_temp_cache()

@app.route('/', methods=['GET'])
def home():
    return render_template("index.html")

@app.route('/api/v1/weather', methods=['GET'])
def get_weather_logs():
    data = get_all_weather()
    return jsonify(data)

@app.route('/api/v1/update', methods=['POST'])
def trigger_update():
    try:
        # 1. Extract
        live_data = fetch_weather_data()
        
        # 2. Archival & File I/O
        archive_raw_data(live_data, ARCHIVE_DIR)
        
        # 3. Transform & Load
        current_weather = live_data['current_weather']
        insert_weather_data(current_weather['temperature'], current_weather['time'])
        
        return jsonify({"status": "success"}), 200

    except APIFetchError as e:
        print(f"Pipeline API Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
        
    except Exception as e:
        print(f"Pipeline System Error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)