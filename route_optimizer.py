from typing import List, Dict
from models import Vehicle, Location, Route, RouteSegment
from api_clients import APIClient

class EmissionCalculator:
    def __init__(self):
        # Emission factors for different vehicle and fuel types (kg CO2/km)
        self.emission_factors = {
            "diesel_truck": 0.9,
            "electric_truck": 0.0,
            "hybrid_truck": 0.6
        }

    def calculate_emissions(self, vehicle: Vehicle, distance: float, 
                          weather_conditions: Dict[str, float]) -> float:
        base_emission = distance * self.emission_factors.get(f"{vehicle.fuel_type}_truck", 0)
        
        # Adjust for weather conditions
        weather_factor = 1.0
        if weather_conditions.get("precipitation", 0) > 0:
            weather_factor *= 1.1  # 10% increase in emissions during rain
        if weather_conditions.get("wind_speed", 0) > 20:
            weather_factor *= 1.15  # 15% increase in high winds
            
        # Adjust for vehicle load
        load_factor = 1.0 + (vehicle.current_load / vehicle.cargo_capacity) * 0.2
        
        return base_emission * weather_factor * load_factor

class RouteOptimizer:
    def __init__(self, traffic_api: APIClient, weather_api: APIClient):
        self.traffic_api = traffic_api
        self.weather_api = weather_api
        self.emission_calculator = EmissionCalculator()

    def optimize_route(self, vehicle: Vehicle, 
                      start: Location, destinations: List[Location]) -> List[Route]:
        possible_routes = []
        current_location = start

        for destination in destinations:
            # Get traffic and route data
            traffic_data = self.traffic_api.get_data(current_location, destination)
            weather_data = self.weather_api.get_data(destination)

            # Calculate route segments
            segment = RouteSegment(
                start=current_location,
                end=destination,
                distance=traffic_data["routes"][0]["summary"]["lengthInMeters"] / 1000,
                duration=traffic_data["routes"][0]["summary"]["travelTimeInSeconds"] / 60,
                traffic_delay=traffic_data["routes"][0]["summary"]["trafficDelayInSeconds"] / 60,
                emissions=0  # Will be calculated later
            )

            # Calculate emissions for this segment
            segment.emissions = self.emission_calculator.calculate_emissions(
                vehicle,
                segment.distance,
                weather_data["weather"]
            )

            # Create route object
            route = Route(
                segments=[segment],
                total_distance=segment.distance,
                total_duration=segment.duration,
                total_emissions=segment.emissions,
                weather_conditions=weather_data["weather"],
                air_quality=weather_data["air"]
            )

            possible_routes.append(route)
            current_location = destination

        return possible_routes