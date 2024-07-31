import typing as t
import hikari
import lightbulb
import sqlite3

from lightbulb.ext import tasks
from lightbulb.ext.tasks import CronTrigger
from datetime import datetime

from bot import get_setting

plugin = lightbulb.Plugin('Update Leaderboard')
leaderboardEco = []
leaderboardEcoLastRefresh = None

@tasks.task(CronTrigger("0,30 * * * *"), auto_start=True)
async def update_leaderboard():
    global leaderboardEco, leaderboardEcoLastRefresh
    leaderboardEco = []
    leaderboardEcoLastRefresh = datetime.now().astimezone()

    try:
        db = sqlite3.connect(get_setting('general', 'database_data_dir'))
        cursor = db.cursor()
        query = "SELECT user_id, balance, tpass FROM economy ORDER BY balance DESC"
        cursor.execute(query)
        results = cursor.fetchall()
    except sqlite3.OperationalError as e:
        results = []

    rank = 0
    lastBalance = None

    for result in results:
        user_id, balance, tpass = result
        if balance != lastBalance:
            rank += 1
            lastBalance = balance
        
        if rank == 1:
            leaderboardEco.append({'user_id': user_id, 'balance': balance, 'tpass': tpass, 'rank': '🥇'})
        elif rank == 2:
            leaderboardEco.append({'user_id': user_id, 'balance': balance, 'tpass': tpass, 'rank': '🥈'})
        elif rank == 3:
            leaderboardEco.append({'user_id': user_id, 'balance': balance, 'tpass': tpass, 'rank': '🥉'})
        else:
            leaderboardEco.append({'user_id': user_id, 'balance': balance, 'tpass': tpass, 'rank': fr'{rank}\.'})
    
    db.commit()
    cursor.close()
    db.close()

@plugin.listener(hikari.StartedEvent)
async def on_start(event: hikari.StartedEvent) -> None:
    await update_leaderboard()

def getLeaderboard() -> list:
    return leaderboardEco

def getLeaderboardLastRefresh() -> datetime:
    return leaderboardEcoLastRefresh

def load(bot):
    bot.add_plugin(plugin)