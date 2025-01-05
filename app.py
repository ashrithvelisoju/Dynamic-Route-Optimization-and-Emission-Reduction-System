import logging
from datetime import datetime
import os
import json
from dotenv import load_dotenv
from typing import List, Dict

from models import Vehicle, Location, Route
from api_clients import TomTomAPI, WeatherAPI
from route_optimizer import RouteOptimizer, EmissionCalculator

class DynamicRoutingSystem:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Setup logging
        self._setup_logging()
        
        # Initialize APIs
        self.tomtom_api_key = os.getenv("TOMTOM_API_KEY")
        self.aqicn_api_key = os.getenv("AQICN_API_KEY")
        
        if not all([self.tomtom_api_key, self.aqicn_api_key]):
            raise ValueError("Missing required API keys in environment variables")
            
        self.tomtom_api = TomTomAPI(self.tomtom_api_key)
        self.weather_api = WeatherAPI(self.aqicn_api_key)
        self.route_optimizer = RouteOptimizer(self.tomtom_api, self.weather_api)
        
        self.logger.info("Dynamic Routing System initialized successfully")

    def _setup_logging(self):
        # Create logger
        self.logger = logging.getLogger('DynamicRoutingSystem')
        self.logger.setLevel(logging.INFO)
        
        # Create console handler
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(handler)

    def plan_route(self, vehicle: Vehicle, start: Location, 
                  destinations: List[Location]) -> List[Route]:
        """Plan optimal routes for the given vehicle and destinations."""
        try:
            self.logger.info(f"Planning route for vehicle {vehicle.id}")
            routes = self.route_optimizer.optimize_route(vehicle, start, destinations)
            self.logger.info(f"Successfully planned route with {len(routes)} segments")
            return routes
        except Exception as e:
            self.logger.error(f"Error planning route: {str(e)}")
            # Return empty list instead of raising exception
            return []

    def get_route_summary(self, route: Route) -> Dict:
        """Generate a summary of the given route."""
        try:
            summary = {
                "total_distance_km": route.total_distance,
                "total_duration_mins": route.total_duration,
                "total_emissions_kg": route.total_emissions,
                "weather_alerts": any(
                    condition > threshold 
                    for condition, threshold in [
                        (route.weather_conditions.get("precipitation", 0), 10),
                        (route.weather_conditions.get("wind_speed", 0), 30)
                    ]
                ),
                "air_quality_alerts": route.air_quality.get("aqi", 0) > 100
            }
            self.logger.info("Route summary generated successfully")
            return summary
        except Exception as e:
            self.logger.error(f"Error generating route summary: {str(e)}")
            return {
                "total_distance_km": 0,
                "total_duration_mins": 0,
                "total_emissions_kg": 0,
                "weather_alerts": False,
                "air_quality_alerts": False
            }

def load_vehicle_data(file_path: str) -> Vehicle:
    """Load vehicle data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return Vehicle(**data)
    except FileNotFoundError:
        raise FileNotFoundError(f"Vehicle data file not found: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in vehicle data file: {file_path}")

def load_locations(file_path: str) -> List[Location]:
    """Load location data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return [Location(**loc) for loc in data]
    except FileNotFoundError:
        raise FileNotFoundError(f"Locations file not found: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in locations file: {file_path}")

def save_route_data(routes: List[Route], file_path: str):
    """Save route data to a JSON file."""
    route_data = []
    for route in routes:
        route_dict = {
            "total_distance": route.total_distance,
            "total_duration": route.total_duration,
            "total_emissions": route.total_emissions,
            "segments": [
                {
                    "start": {"lat": seg.start.lat, "lon": seg.start.lon, "address": seg.start.address},
                    "end": {"lat": seg.end.lat, "lon": seg.end.lon, "address": seg.end.address},
                    "distance": seg.distance,
                    "duration": seg.duration,
                    "emissions": seg.emissions
                }
                for seg in route.segments
            ]
        }
        route_data.append(route_dict)
    
    with open(file_path, 'w') as f:
        json.dump(route_data, f, indent=2)

def main():
    """Main function to run the Dynamic Route Optimization System."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    try:
        # Initialize the system
        logger.info("Initializing Dynamic Route Optimization System")
        system = DynamicRoutingSystem()

        # Load vehicle data
        vehicle_file = "vehicle_data.json"
        try:
            vehicle = load_vehicle_data(vehicle_file)
            logger.info(f"Loaded vehicle data for vehicle ID: {vehicle.id}")
        except Exception as e:
            logger.error(f"Error loading vehicle data: {str(e)}")
            return

        # Load location data
        locations_file = "locations.json"
        try:
            locations = load_locations(locations_file)
            logger.info(f"Loaded {len(locations)} locations")
        except Exception as e:
            logger.error(f"Error loading locations: {str(e)}")
            return

        # Plan routes
        try:
            start_location = locations[0]  # First location is starting point
            destinations = locations[1:]    # Remaining locations are destinations
            
            logger.info("Planning routes...")
            routes = system.plan_route(vehicle, start_location, destinations)
            
            # Generate and log summaries
            for i, route in enumerate(routes, 1):
                summary = system.get_route_summary(route)
                logger.info(f"Route {i} Summary:")
                logger.info(f"Distance: {summary['total_distance_km']:.2f} km")
                logger.info(f"Duration: {summary['total_duration_mins']:.2f} minutes")
                logger.info(f"Emissions: {summary['total_emissions_kg']:.2f} kg CO2")
                
                if summary['weather_alerts']:
                    logger.warning(f"Weather alerts present for route {i}")
                if summary['air_quality_alerts']:
                    logger.warning(f"Air quality alerts present for route {i}")

            # Save route data
            output_file = "route_output.json"
            save_route_data(routes, output_file)
            logger.info(f"Route data saved to {output_file}")

        except Exception as e:
            logger.error(f"Error during route planning: {str(e)}")
            return

    except Exception as e:
        logger.error(f"System initialization error: {str(e)}")
        return

if __name__ == "__main__":
    main()