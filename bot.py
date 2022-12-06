import os
import hikari
import lightbulb
import miru
import sqlite3

import start

TOKEN = startup.TOKEN
DEFAULT_GUILD_ID = startup.DEFAULT_GUILD_ID

bot = lightbulb.BotApp(
    token=TOKEN,
    default_enabled_guilds=DEFAULT_GUILD_ID,
    prefix='!',
    intents=hikari.Intents.ALL
)   

@bot.listen()
async def on_ready(event: hikari.StartedEvent) -> None:
    db = sqlite3.connect('database.sqlite')
    cursor = db.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS database (
        user_id INTEGER, 
        balance INTEGER,
        total INTEGER,
        tpass INTEGER
    )''')

if __name__ == '__main__':
    if os.name != 'nt':
        import uvloop
        uvloop.install()
    miru.load(bot)
    bot.load_extensions_from('./extentions')
    bot.run(status=hikari.Status.DO_NOT_DISTURB, activity=hikari.Activity(name='Type /info for help!', type=hikari.ActivityType.STREAMING, url='https://www.twitch.tv/ryqb'))
