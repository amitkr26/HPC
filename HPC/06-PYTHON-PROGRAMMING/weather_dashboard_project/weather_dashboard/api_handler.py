import requests

API_URL = ("https://api.open-meteo.com/v1/forecast"
           "?latitude=52.52&longitude=13.41&current_weather=true")


class APIFetchError(Exception):
    """Raised when the weather API cannot be reached or returns a bad response."""
    pass


def fetch_weather(url=API_URL, timeout=10):
    """Call the weather API and return the parsed JSON as a dictionary."""
    try:
        response = requests.get(url, timeout=timeout)

        if response.status_code != 200:
            raise APIFetchError(f"API returned status code {response.status_code}")

        data = response.json()

        # make sure the response has the part we actually need
        assert "current_weather" in data, "'current_weather' key missing in API response"

        return data

    except (requests.exceptions.RequestException, ValueError) as error:
        # network drop, timeout, bad JSON, etc.
        raise APIFetchError(f"Could not fetch data from API: {error}") from error

    finally:
        print("API connection attempt finished.")


if __name__ == "__main__":
    # local test only - runs when this file is executed directly
    try:
        result = fetch_weather()
        print("Fetched:", result["current_weather"])
    except (APIFetchError, AssertionError) as error:
        print("Test failed:", error)
