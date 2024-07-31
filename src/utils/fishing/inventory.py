import sqlite3
import hikari

from bot import get_setting
from utils.fishing.bait import Bait
from utils.fishing.config_loader import FishingConfigLoader

class Inventory:
    def __init__(self, user: hikari.User) -> None:
        """
        Initialize a new Inventory instance.

        Parameters
        ----------
        user : hikari.User
            The user whose inventory is being managed.
        """
        self.db = sqlite3.connect(get_setting('general', 'database_data_dir'))
        self.cursor = self.db.cursor()
        self.user = user

    def get_baits(self) -> list[Bait]:
        """Get the bait inventory of a user."""
        self.cursor.execute('''
            SELECT bait_id, amount FROM fishing
            WHERE user_id = ?
        ''', (self.user.id,))
        result = self.cursor.fetchall()
        return [FishingConfigLoader.find_bait_by_id(id) for id, _ in result] 
    
    def get_bait_amount(self, bait: Bait) -> int:
        """Get the amount of a specific bait in the inventory of a user."""
        self.cursor.execute('''
            SELECT amount FROM fishing
            WHERE user_id = ? AND bait_id = ?
        ''', (self.user.id, bait.id))
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def update_bait(self, bait: Bait, amount: int) -> None:
        """Update the bait from the inventory of a user."""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO fishing (user_id, bait_id, amount)
                VALUES (?, ?, ?)
            ''', (self.user.id, bait.id, amount))
            self.db.commit()
        except sqlite3.Error as e:
            self.db.rollback()
            print("Error inserting item from the database:", e)
    
    def delete_bait(self, bait: Bait) -> None:
        """Delete a bait from the inventory of a user."""
        try:
            self.cursor.execute('''
                DELETE FROM fishing
                WHERE user_id = ? AND bait_id = ?
            ''', (self.user.id, bait.id))
            self.db.commit()
        except sqlite3.Error as e:
            self.db.rollback()
            print("Error inserting item from the database:", e)
    
    def __delattr__(self) -> None:
        """Close the database connection when the object is deleted."""
        self.db.close()