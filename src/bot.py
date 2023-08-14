import os
import json
import io
import subprocess
import sys
import hikari
import lightbulb
import miru
import sqlite3
import startup

from lightbulb.ext import tasks

VERSION = startup.VERSION
TOKEN = startup.TOKEN
DEFAULT_GUILD_ID = startup.DEFAULT_GUILD_ID
WORDNIK_API_KEY = startup.WORDNIK_API_KEY

# Create a bot instance

bot = lightbulb.BotApp(
    token=TOKEN,
    default_enabled_guilds=DEFAULT_GUILD_ID,
    prefix='!',
    help_class=None,
    intents=hikari.Intents.ALL,
)   

# Create a database

@bot.listen()
async def on_ready(event: hikari.StartedEvent) -> None:
    if not os.path.exists('database'):
        os.makedirs('database')

    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor() # checks if db exists
    cursor.execute('''CREATE TABLE IF NOT EXISTS economy (
        user_id INTEGER, 
        balance INTEGER,
        total INTEGER,
        loss INTEGER,
        tpass INTEGER
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cards (
        id TEXT PRIMARY KEY, 
        user_id TEXT,
        date TEXT, 
        name TEXT, 
        pokemon_id INTEGER, 
        rarity INTEGER, 
        shiny INTEGER,
        favorite INTEGER
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
        id TEXT PRIMARY KEY, 
        user_id TEXT, 
        date TEXT,
        type TEXT
    )''')

    # Generate settings.json if not found
    if not os.path.isfile('settings.json') or not os.access('settings.json', os.R_OK): # checks if file exists
        print ('Either file is missing or is not readable, creating file...')
        
        dictionary = {
            "database_data_dir": 'database/database.sqlite',
            'rushsite_register_link': 'https://bit.ly/3tH1nI2',
            'starting_balance': 1000,
            'starting_tux_pass': 0,
            'pokemon_pack_amount': 7,
            'pokemon_max_capacity': 2000,
            'command_cooldown': 5,
            'embed_color': '#249EDB',
            'embed_important_color': 'b03f58',
            'embed_success_color': '#32CD32',
            'embed_error_color': '#FF0000',
            'auto_translate': False,
        }
        
        with io.open(os.path.join('', 'settings.json'), 'w') as openfile:
            openfile.write(json.dumps(dictionary, indent=4))

# Register user to database

@bot.listen(hikari.MessageCreateEvent) 
async def on_message(event: hikari.MessageCreateEvent):
    if event.is_bot or not event.content: # if bot sent the message
        return
    
    user = event.author
    
    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    
    if verify_user(user) == None: # if user has never been register
        sql = ('INSERT INTO economy(user_id, balance, total, loss, tpass) VALUES (?,?,?,?,?)')
        val = (user.id, get_setting('starting_balance'), get_setting('starting_balance'), 0, get_setting('starting_tux_pass'))
        cursor.execute(sql, val) 
    
    db.commit() # saves changes
    cursor.close()
    db.close()

## Functions ##

def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def get_setting(option: str):
    with open('settings.json', 'r') as openfile:
        settings = dict(json.load(openfile))
        
        return settings[option]

def write_setting(option: str, value):
    with open('settings.json', 'r') as openfile:
        data = json.load(openfile)

    data[option] = value

    with open('settings.json', 'w') as openfile:
        json.dump(data, openfile, indent=4)

def verify_user(user: hikari.User):
    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    
    cursor.execute(f'SELECT user_id FROM economy WHERE user_id = {user.id}') # moves cursor to user's id from database
    result = cursor.fetchone() # grabs the value of user's id
    
    return result

def get_commands(bot: lightbulb.BotApp) -> dict:
    commandList = {}
    filter = []
    for cmd in bot._slash_commands.keys():
        if cmd not in filter:
            group = bot.get_slash_command(cmd).plugin.name
            description = bot.get_slash_command(cmd).description

            if group in commandList:
                commandList[group].append((cmd, description))
            else:
                commandList[group] = [(cmd, description)]
    return commandList

## Script ##

if __name__ == '__main__':
    # Install uvloop for Linux users
    if os.name != 'nt':
        install('uvloop')
        import uvloop
        uvloop.install()

    # Release the bot!
    miru.install(bot)
    tasks.load(bot)
    bot.load_extensions_from('./extentions')
    bot.run(
        status=hikari.Status.DO_NOT_DISTURB, 
        activity=hikari.Activity(name='Type /help for info!', type=hikari.ActivityType.STREAMING, url='https://www.twitch.tv/ryqb')
    )