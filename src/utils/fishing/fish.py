import random

from bot import get_setting
from utils.fishing.bait import Bait

class Fish():
    def __init__(self, id: str, name: str, emoji: str, description: str, price: float, salvage: list[Bait], weight: int, min: int, max: int) -> None:
        """
        Initialize a new Fish instance.

        Parameters
        ----------
        id : str
            The ID of the fish.
        name : str
            The name of the fish.
        emoji : str
            The emoji representing the fish.
        description : str
            A description of the fish.
        price : float
            The price of the fish.
        salvage : list[Bait]
            The bait that can be salvaged from the fish.
        rarity : int
            The rarity of the fish.
        weight : int
            The weight of the fish.
        min : int
            The minimum size of the fish.
        max : int
            The maximum size of the fish.
        """
        self.id = id
        self.name = name
        self.emoji = emoji
        self.description = description
        self.price = price
        self.salvage = salvage
        self.weight = weight
        self.min = min
        self.max = max

    def get_fish_quantity(self, quantityBonus: float) -> int:
        """Get the quantity of fish caught with a specific bait and weather."""
        base = random.randint(self.min, self.max)
        bonus = base * quantityBonus
        return round(base + bonus)

    def get_salvage_quantity(self, count: int) -> int:
        """Get the quantity of bait salvaged from the fish."""
        min = get_setting('fishing', 'salvage_rate_min')
        max = get_setting('fishing', 'salvage_rate_max')
        salvage_rate = random.uniform(min, max)
        return round(count * salvage_rate)

    def get_rarity(self) -> str:
        """Get the rarity of the fish based on its weight."""
        if self.weight < 20:
            return 'Rare'
        elif self.weight < 40:
            return 'Uncommon'
        return 'Common'

    def combine_salvages(self, quantity: int, randomize: bool = False) -> list[tuple[Bait, int]]:
        salvages = [bait for bait in self.salvage for _ in range(quantity)]
        combinedSalvages = {}
        for bait in salvages:
            if bait in combinedSalvages:
                combinedSalvages[bait] += 1
            else:
                combinedSalvages[bait] = 1

        if randomize:
            combinedSalvages = {bait: self.get_salvage_quantity(count) for bait, count in combinedSalvages.items()}

        return [(bait, count) for bait, count in combinedSalvages.items()]

    @staticmethod
    def load_fish_from_config(fish_data, bait_instances):
        """Load fish data from a configuration file."""
        return {
            key: Fish(
                id=key,
                name=item['name'],
                emoji=item['emoji'],
                description=item['description'],
                price=item['price'],
                salvage=[bait_instances[bait_id] for bait_id in item.get('salvage', []) if bait_id in bait_instances],
                weight=item['weight'],
                min=item['min'],
                max=item['max']
            )
            for key, item in fish_data.items()
        }
    
    def to_dict(self) -> dict:
        """Convert the fish to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'emoji': self.emoji,
            'description': self.description,
            'price': self.price,
            'salvage': [bait.id for bait in self.salvage],
            'weight': self.weight,
            'min': self.min,
            'max': self.max
        }

    def __str__(self) -> str:
        salvage = ', '.join(f'{bait.emoji} {bait.name}' for bait in self.salvage) if self.salvage else 'None'
        return (
            f'[{self.id}] {self.emoji} {self.name}: {self.description}, '
            f'Price: 🪙 {self.price}, Weight: {self.weight}, '
            f'Min: {self.min}, Max: {self.max}\n'
            f'Salvage: {salvage}'
        )