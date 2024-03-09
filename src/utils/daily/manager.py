import hikari
import sqlite3

from datetime import datetime, timedelta
import pytz

from bot import get_setting

class DailyManager:
    def __init__(self, user: hikari.User) -> None:
        self.db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        self.cursor = self.db.cursor()
        self.user = user
        self.streak, self.date, self.today, self.yesterday = self.get_daily_info()

    def update_streak(self) -> None:
        if self.date == self.yesterday:
            self.streak += 1 if self.streak < 20 else 0
        else:
            self.streak = 1
        
        self.update_streak_sqlite()

    def update_streak_sqlite(self) -> None:
        db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        cursor = db.cursor()

        cursor.execute(f'SELECT streak, date FROM economy WHERE user_id = {self.user.id}')
        val = cursor.fetchone() 

        sql = ('UPDATE economy SET streak = ?, date = ? WHERE user_id = ?')
        val = (self.streak, self.today, self.user.id)
        
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        db.close()
    
    def on_cooldown(self) -> None:
        return self.date == self.today
    
    def get_daily_info(self):
        timezone = pytz.timezone('America/New_York')
        today = datetime.now(timezone).strftime('%Y-%m-%d')
        yesterday = (datetime.now(timezone) - timedelta(days=1)).strftime('%Y-%m-%d')
        self.cursor.execute(f'SELECT streak, date FROM economy WHERE user_id = {self.user.id}')
        streak, date = self.cursor.fetchone()

        return (streak, date, today, yesterday)