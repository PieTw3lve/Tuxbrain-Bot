import json

class Weather:
    def __init__(self, id: str, name: str, emoji: str, description: str, weight: int, success_rate_bonus: float, quantity_bonus: float, rarity_bonus: float) -> None:
        """
        Initialize a new Weather instance.

        Parameters
        ----------
        id : str
            The ID of the weather.
        name : str
            The name of the weather.
        emoji : str
            The emoji representing the weather.
        description : str
            A description of the weather.
        rarity : Rarity
            The rarity of the weather.
        weight : int
            The weight of the weather.
        success_rate_bonus : int
            The bonus success rate of catching a fish.
        quantity_bonus : int
            The bonus quantity of fish caught.
        rarity_bonus : int
            The bonus rarity of fish caught.
        """
        self.id = id
        self.name = name
        self.emoji = emoji
        self.description = description
        self.weight = weight
        self.success_rate_bonus = success_rate_bonus
        self.quantity_bonus = quantity_bonus
        self.rarity_bonus = rarity_bonus

    @staticmethod
    def load_weather_from_config(weather_data):
        """Load weather data from a configuration file."""
        return {key: Weather(id=key, **item) for key, item in weather_data.items()}

    def to_dict(self) -> dict:
        """Convert the weather to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'emoji': self.emoji,
            'description': self.description,
            'weight': self.weight,
            'success_rate_bonus': self.success_rate_bonus,
            'quantity_bonus': self.quantity_bonus,
            'rarity_bonus': self.rarity_bonus
        }

    def __str__(self) -> str:
        return (
            f'[{self.id}] {self.emoji} {self.name}: {self.description}, Weight: {self.weight}, '
            f'Success Rate Bonus: {self.success_rate_bonus * 100}%, Quantity Bonus: {self.quantity_bonus * 100}%, '
            f'Rarity Bonus: {self.rarity_bonus * 100}%'
        )