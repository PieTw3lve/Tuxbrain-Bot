import random

from utils.fishing.bait import Bait
from utils.fishing.fish import Fish
from utils.fishing.weather import Weather

class Location:
    def __init__(self, id: str, name: str, emoji: str, description: str, fish: list[Fish], success_rate_bonus: float, quantity_bonus: float, rarity_bonus: float) -> None:
        """
        Initialize a new Location instance.

        Parameters
        ----------
        name : str
            The name of the location.
        emoji : str
            The emoji representing the location.
        description : str
            A description of the location.
        fish : list[Fish]
            The fish that can be caught in the location.
        weather : list[Weather]
            The available weather conditions in the location.
        success_rate_bonus : float
            The bonus success rate of catching a fish.
        quantity_bonus : float
            The bonus quantity of fish caught.
        rarity_bonus : float
            The bonus rarity of fish caught.
        """
        self.id = id
        self.name = name
        self.emoji = emoji
        self.description = description
        self.fish = sorted(fish, key=lambda fish: (fish.weight, -fish.price), reverse=True)
        self.success_rate_bonus = success_rate_bonus
        self.quantity_bonus = quantity_bonus
        self.rarity_bonus = rarity_bonus
        self.baseWeights = [fish.weight for fish in self.fish]
    
    def get_fish(self, bait: Bait, weather: Weather) -> Fish:
        """Get a fish that can be caught with a specific bait and weather."""
        successChance =  bait.success_rate_bonus + weather.success_rate_bonus + self.success_rate_bonus
        rarityBonus = bait.rarity_bonus + weather.rarity_bonus + self.rarity_bonus

        fishWeights = self.get_fish_adjusted_weights(rarityBonus)

        if random.uniform(0, 1) > successChance or sum(fishWeights.values()) == 0:
            return None

        fish = random.choices(self.fish, weights=fishWeights.values(), k=1)[0]

        return fish
    
    def get_fish_rarity(self, fish: Fish, weather: Weather) -> str:
        """Get the rarity of a fish based on the location and weather."""
        rarityBonus = weather.rarity_bonus + self.rarity_bonus
        fishWeights = self.get_fish_adjusted_weights(rarityBonus)
        totalWeight = sum(fishWeights.values())

        if totalWeight != 0:
            for fishItem, weight in fishWeights.items():
                if fish.id == fishItem.id:
                    percentage = (weight / totalWeight) * 100
                    rarityMap = {
                        (0, 3): 'Legendary',
                        (3, 10): 'Rare',
                        (10, 15): 'Uncommon',
                        (15, float('inf')): 'Common'
                    }
                    for (low, high), rarity in rarityMap.items():
                        if low < percentage <= high:
                            return rarity

        return 'Impossible'

    def get_fish_adjusted_weights(self, rarityBonus: float) -> dict[Fish, list[int]]:
        """Get the percentage of each fish that can be caught in the location."""
        rarityBonus = rarityBonus * 100
        rarityAdjustments = [(1 / weight) * rarityBonus for weight in self.baseWeights]
        adjustedWeights = [max(0, weight + (weight * adj)) for weight, adj in zip(self.baseWeights, rarityAdjustments)]
        return {fish: weight for fish, weight in zip(self.fish, adjustedWeights)}
    
    def print_fish_percentages(self, rarityBonus: float) -> None:
        """Print the percentage of each fish that can be caught in the location."""
        adjustedWeights = self.get_fish_adjusted_weights(rarityBonus).values()
        print(f'Fish Percentages ({(rarityBonus * 100) + 100:.2f}%):')
        for fish, base, adjusted in zip(self.fish, self.baseWeights, adjustedWeights):
            basePercentage = (base / sum(self.baseWeights)) * 100 if sum(self.baseWeights) > 0 else 0
            adjustedPercentage = (adjusted / sum(adjustedWeights)) * 100 if sum(adjustedWeights) > 0 else 0
            print(f'{fish.emoji} {fish.name}: {basePercentage:.2f}% -> {adjustedPercentage:.2f}%', end='\n')

    @staticmethod
    def load_location_from_config(location, fish) -> dict[str, 'Location']:
        """Load location data from a configuration file."""
        return {
            key: Location(
                id=key,
                name=item['name'],
                emoji=item['emoji'],
                description=item['description'],
                fish=[fish[id] for id in item.get('fish', []) if id in fish],
                success_rate_bonus=item['success_rate_bonus'],
                quantity_bonus=item['quantity_bonus'],
                rarity_bonus=item['rarity_bonus']
            )
            for key, item in location.items()
        }
    
    def to_dict(self) -> dict:
        """Convert the location to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'emoji': self.emoji,
            'description': self.description,
            'fish': [fish.id for fish in self.fish],
            'success_rate_bonus': self.success_rate_bonus,
            'quantity_bonus': self.quantity_bonus,
            'rarity_bonus': self.rarity_bonus
        }

    def __str__(self) -> str:
        fish = ', '.join(f'{fish.emoji} {fish.name}' for fish in self.fish) if self.fish else 'None'
        weather = ', '.join(f'{weather.emoji} {weather.name}' for weather in self.weather) if self.weather else 'None'
        return (
            f'[{self.id}] {self.emoji} {self.name}: {self.description}\n'
            f'Success Rate Bonus: {self.success_rate_bonus * 100}%, Quantity Bonus: {self.quantity_bonus * 100}%, '
            f'Rarity Bonus: {self.rarity_bonus * 100}%\n'
            f'Fish: {fish}\n'
            f'Weather: {weather}'
        )