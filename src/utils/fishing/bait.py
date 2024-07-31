from datetime import datetime
from enum import Enum

class Days(Enum):
    SATURDAY = 'Saturday'
    SUNDAY = 'Sunday'

class Bait:
    def __init__(self, id: str, name: str, emoji: str, description: str, tooltip: str, price: float, success_rate_bonus: float, quantity_bonus: float, rarity_bonus: float) -> None:
        """
        Initialize a new Bait instance.

        Parameters
        ----------
        id : str
            The ID of the bait.
        name : str
            The name of the bait.
        emoji : str
            The emoji representing the bait.
        price : float
            The price of the bait.
        description : str
            A description of the bait.
        tooltip : str
            A tooltip for the bait.
        success_rate_bonus : int
            The success rate of catching a fish with this bait.
        quantity_bonus : int
            The bonus quantity of fish caught with this bait.
        rarity_bonus : int
            The bonus rarity of fish caught with this bait.
        """
        self.id = id
        self.name = name
        self.emoji = emoji
        self.price = price
        self.description = description
        self.tooltip = tooltip
        self.success_rate_bonus = success_rate_bonus
        self.quantity_bonus = quantity_bonus 
        self.rarity_bonus = rarity_bonus
    
    def current_price(self) -> float:
        """Calculate the current price, applying a discount if it's Saturday or Sunday."""
        today = datetime.now().strftime('%A')
        if today in [Days.SATURDAY.value, Days.SUNDAY.value]:
            return round(self.price * 0.7, 2)  # Apply 30% discount
        return self.price
    
    @staticmethod
    def load_bait_from_config(bait_data):
        """Load bait data from a configuration file."""
        return {key: Bait(id=key, **item) for key, item in bait_data.items()}
    
    def to_dict(self) -> dict:
        """Convert the bait to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'emoji': self.emoji,
            'price': self.price,
            'description': self.description,
            'tooltip': self.tooltip,
            'success_rate_bonus': self.success_rate_bonus,
            'quantity_bonus': self.quantity_bonus,
            'rarity_bonus': self.rarity_bonus
        }

    def __str__(self) -> str:
        return (
            f'[{self.id}] {self.emoji} {self.name}: {self.description}, '
            f'Price: 🪙 {self.current_price()}, Success Rate: {self.success_rate_bonus * 100}%, '
            f'Quantity Bonus: {self.quantity_bonus * 100}%, Rarity Bonus: {self.rarity_bonus * 100}%'
        )