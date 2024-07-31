import json

from utils.fishing.bait import Bait
from utils.fishing.fish import Fish
from utils.fishing.weather import Weather
from utils.fishing.location import Location

class FishingConfigLoader:
    def __init__(self, path='settings.json'):
        self.path = path
        self.baits = {}
        self.fishes = {}
        self.weathers = {}
        self.locations = {}
        self.load_fishing_data()
    
    def load_fishing_data(self) -> None:
        """Load fishing data from a configuration file."""
        with open('settings.json', 'r') as file:
            config = json.load(file)

        bait = config.get('fishing', {}).get('bait', {})
        fish = config.get('fishing', {}).get('fish', {})
        weather = config.get('fishing', {}).get('weather', {})
        location = config.get('fishing', {}).get('location', {})

        self.baits = Bait.load_bait_from_config(bait)
        self.fishes = Fish.load_fish_from_config(fish, self.baits)
        self.weathers = Weather.load_weather_from_config(weather)
        self.locations = Location.load_location_from_config(location, self.fishes)

    @classmethod
    def find_bait_by_id(cls, bait_id) -> Bait:
        """Find a bait instance from its ID."""
        for bait in cls().baits.values():
            if bait.id == bait_id:
                return bait
    
    @classmethod
    def find_fish_from_id(cls, fish_id) -> Fish:
        """Find a fish instance from its ID."""
        for fish in cls().fishes.values():
            if fish.id == fish_id:
                return fish
    
    @classmethod
    def find_weather_from_id(cls, weather_id) -> Weather:
        """Find a weather instance from its ID."""
        for weather in cls().weathers.values():
            if weather.id == weather_id:
                return weather
    
    @classmethod
    def find_location_from_id(cls, location_id) -> Location:
        """Find a location instance from its ID."""
        for location in cls().locations.values():
            if location.id == location_id:
                return location

    def __str__(self) -> str:
        bait = '\n'.join(str(bait) for bait in self.baits.values())
        fish = '\n'.join(str(fish) for fish in self.fishes.values())
        weather = '\n'.join(str(weather) for weather in self.weathers.values())
        locations = '\n'.join(str(location) for location in self.locations.values())
        return (
            f'Bait:\n{bait}\n'
            f'Fish:\n{fish}\n'
            f'Weather:\n{weather}\n'
            f'Locations:\n{locations}'
        )