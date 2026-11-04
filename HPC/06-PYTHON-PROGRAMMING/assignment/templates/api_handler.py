import requests

class APIFetchError(Exception):
    pass

def fetch_weather_data():
    url = "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true"
    
    try:
        response = requests.get(url)
        
        if response.status_code != 200:
            raise APIFetchError(f"HTTP Error: Received status code {response.status_code}")
            
        data = response.json()
        
        # Verify the exact data structure before returning it
        assert "current_weather" in data, "Key 'current_weather' missing from API response"
        
        return data

    except requests.exceptions.RequestException as e:
        # Catch network drops, DNS failures, etc., and repackage them
        raise APIFetchError(f"Network failure: {e}")
        
    finally:
        print("Network process: API connection attempt finished.")

if __name__ == '__main__':
    # Local testing isolation
    print(fetch_weather_data())