from abc import ABC, abstractmethod
from typing import Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from models import Location
from time import sleep

class APIClient(ABC):
    def __init__(self):
        self.session = self._create_session()
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        
        # Define retry strategy
        retry_strategy = Retry(
            total=3,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4 seconds between retries
            status_forcelist=[408, 429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @abstractmethod
    def get_data(self, *args, **kwargs):
        pass

class TomTomAPI(APIClient):
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://api.tomtom.com/routing/1"

    def get_data(self, start: Location, end: Location) -> Dict[str, Any]:
        try:
            endpoint = f"{self.base_url}/calculateRoute/{start.lat},{start.lon}:{end.lat},{end.lon}/json"
            params = {
                "key": self.api_key,
                "traffic": "true",
                "travelMode": "truck"
            }
            
            response = self.session.get(
                endpoint, 
                params=params, 
                timeout=(5, 15)  # (connect timeout, read timeout)
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout connecting to TomTom API")
            # Return simulated data for testing
            return self._get_simulated_route_data(start, end)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error connecting to TomTom API: {str(e)}")
            return self._get_simulated_route_data(start, end)

    def _get_simulated_route_data(self, start: Location, end: Location) -> Dict[str, Any]:
        """Provide simulated data when API is unavailable"""
        return {
            "routes": [{
                "summary": {
                    "lengthInMeters": 50000,  # 50 km
                    "travelTimeInSeconds": 3600,  # 1 hour
                    "trafficDelayInSeconds": 300  # 5 minutes delay
                }
            }]
        }

class WeatherAPI(APIClient):
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://api.aqicn.org/v2"

    def get_data(self, location: Location) -> Dict[str, Any]:
        try:
            endpoint = f"{self.base_url}/nearest"
            params = {
                "token": self.api_key,
                "lat": location.lat,
                "lon": location.lon
            }
            
            response = self.session.get(
                endpoint, 
                params=params,
                timeout=(5, 15)  # (connect timeout, read timeout)
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout connecting to Weather API")
            return self._get_simulated_weather_data()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error connecting to Weather API: {str(e)}")
            return self._get_simulated_weather_data()

    def _get_simulated_weather_data(self) -> Dict[str, Any]:
        """Provide simulated data when API is unavailable"""
        return {
            "weather": {
                "precipitation": 0,
                "wind_speed": 10,
                "temperature": 25
            },
            "air": {
                "aqi": 50
            }
        }