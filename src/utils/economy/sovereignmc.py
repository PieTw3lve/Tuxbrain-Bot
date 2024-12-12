import sqlite3

from bot import get_setting

class SovManager:
    def __init__(self):
        self.db = sqlite3.connect(get_setting('general', 'database_data_dir'))
        self.cursor = self.db.cursor()
    
    def __del__(self):
        self.db.close()

    def create_table(self):
        self.cursor.execute('CREATE TABLE IF NOT EXISTS sovereignmc (user_id INTEGER PRIMARY KEY, coins INTEGER)')
        self.db.commit()

    def get_coins(self, user_id: int) -> int:
        self.cursor.execute(f'SELECT coins FROM sovereignmc WHERE user_id = {user_id}')
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def set_coins(self, user_id: int, coins: int) -> None:
        self.cursor.execute(f'SELECT coins FROM sovereignmc WHERE user_id = {user_id}')
        result = self.cursor.fetchone()
        
        if result:
            self.cursor.execute(f'UPDATE sovereignmc SET coins = {coins} WHERE user_id = {user_id}')
        else:
            self.cursor.execute(f'INSERT INTO sovereignmc (user_id, coins) VALUES ({user_id}, {coins})')
        
        self.db.commit()
    
    def reset_database(self) -> None:
        self.cursor.execute('DROP TABLE IF EXISTS sovereignmc')
        self.db.commit()