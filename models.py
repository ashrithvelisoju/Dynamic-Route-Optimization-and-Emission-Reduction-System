from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Vehicle:
    id: str
    type: str
    fuel_type: str
    fuel_efficiency: float  # km/L
    cargo_capacity: float   # kg
    current_load: float    # kg

@dataclass
class Location:
    lat: float
    lon: float
    address: str

@dataclass
class RouteSegment:
    start: Location
    end: Location
    distance: float    # km
    duration: float    # minutes
    traffic_delay: float  # minutes
    emissions: float   # kg CO2

@dataclass
class Route:
    segments: List[RouteSegment]
    total_distance: float
    total_duration: float
    total_emissions: float
    weather_conditions: Dict[str, float]
    air_quality: Dict[str, float]