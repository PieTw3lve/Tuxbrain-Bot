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
    help_class=None,
    intents=hikari.Intents.ALL,
)   

# Create a database

@bot.listen()
async def on_ready(event: hikari.StartedEvent) -> None:
    # Generate database directory if not found
    if not os.path.exists('database'):
        os.makedirs('database')
    
    # Generate settings.json if not found
    if not os.path.isfile('settings.json') or not os.access('settings.json', os.R_OK): # checks if file exists
        print ('Either file is missing or is not readable, creating file...')

        dictionary = get_setting_json()
        
        with io.open(os.path.join('', 'settings.json'), 'w') as openfile:
            openfile.write(json.dumps(dictionary, indent=4))

    db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
    cursor = db.cursor() # checks if db exists
    cursor.execute('''CREATE TABLE IF NOT EXISTS economy (
        user_id INTEGER, 
        balance INTEGER,
        total INTEGER,
        loss INTEGER,
        tpass INTEGER,
        streak INTEGER,
        date TEXT,
        level INTEGER,
        experience INTEGER
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pokemon (
        id TEXT PRIMARY KEY, 
        user_id TEXT,
        date TEXT, 
        name TEXT, 
        pokemon_id INTEGER, 
        rarity INTEGER, 
        shiny INTEGER,
        favorite INTEGER
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS profile (
        user_id TEXT,
        name TEXT, 
        type TEXT,
        active INTEGER,
        PRIMARY KEY (user_id, type, name)
    )''')

# Register user to database

@bot.listen(hikari.MessageCreateEvent) 
async def on_message(event: hikari.MessageCreateEvent):
    if event.is_bot or not event.content: # if bot sent the message
        return
    
    user = event.author
    
    db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
    cursor = db.cursor()
    
    if verify_user(user) == None: # if user has never been register
        sql = ('INSERT INTO economy(user_id, balance, total, loss, tpass, streak, date, level, experience) VALUES (?,?,?,?,?,?,?,?,?)')
        val = (user.id, get_setting('economy', 'starting_balance'), get_setting('economy', 'starting_balance'), 0, get_setting('economy', 'starting_tux_pass'), 0, None, 0, 0)
        cursor.execute(sql, val) 
    
    db.commit() # saves changes
    cursor.close()
    db.close()

## Functions ##

def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def get_setting_json():
    settings = {
        'database_data_dir': 'database/database.sqlite',
        'command_cooldown': 5,
        'embed_color': '#249EDB',
        'embed_important_color': 'b03f58',
        'embed_success_color': '#32CD32',
        'embed_error_color': '#FF0000',
        'auto_translate': True,
        'auto_translate_conf': 0.80,
        'auto_translate_min_relative_distance': 0.90
    }
    roles = {
        'owner_role_id': 1000000000000000000,
        'admin_role_id': 1000000000000000000,
        'staff_role_id': 1000000000000000000,
        'rushsite_s1_id': 1000000000000000000,
        'rushsite_s2_id': 1000000000000000000,
        'rushsite_s3_id': 1000000000000000000,
        'rushsite_s4_id': 1000000000000000000,
        'rushsite_s5_id': 1000000000000000000,
    }
    economy = {
        'starting_balance': 1000,
        'starting_tux_pass': 0,
    }
    profile = {
        'coin': {
            'gray-banner': 200,
            'float-nametag': 200,
            'seperator-nametag': 200,
            'tuxedo-nametag': 200,
            'apple-base': 500,
            'burgundy-base': 500,
            'blueberry-base': 500,
            'grape-base': 500,
            'snow-base': 1000,
            'snow-nametag': 1000,
            'plastic-banner': 1000,
            'plastic-base': 1000,
            'plastic-nametag': 1000,
            'blue-banner': 2000,
            'orange-banner': 2000,
            'grassiant-banner': 5000,
            'sky-banner': 5000,
            'purp-banner': 5000,
            'purp-base': 5000,
            'purp-nametag': 5000,
            'charged_rose-banner': 5000,
            'rushsite_s3-banner': 7000,
            'france-banner': 10000,
            'usa-banner': 10000
            },
            'tpass': {
                'nippuwu-banner': 1
            }
        }
    pokemon = {
        'pokemon_pack_amount': 7,
        'pokemon_max_capacity': 2000,
    }
    
    json = {
        'settings': settings,
        'roles': roles,
        'economy': economy,
        'profile': profile,
        'pokemon': pokemon,
    }
        
    return json

def get_setting(section: str, option: str = None):
    with open('settings.json', 'r') as openfile:
        data = json.load(openfile)
        if option:
            if section in data and option in data[section]:
                return data[section][option]
            else:
                return None
        elif section in data:
            return data[section]
        else:
            return None

def write_setting(section: str, option: str, value):
    with open('settings.json', 'r') as openfile:
        data = json.load(openfile)

    if section not in data:
        data[section] = {}

    data[section][option] = value

    with open('settings.json', 'w') as openfile:
        json.dump(data, openfile, indent=4)

def verify_user(user: hikari.User):
    db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
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
        activity=hikari.Activity(name='Rushsite Season 4', type=hikari.ActivityType.STREAMING, url='https://www.twitch.tv/ryqb')
    )
    