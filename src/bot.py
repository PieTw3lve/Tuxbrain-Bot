import os
import json
import io
import subprocess
import sys
import hikari
import lightbulb
import miru
import sqlite3

from lightbulb.ext import tasks

VERSION = '1.3.0'

## Functions ##

def install(package):
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def get_setting_json():
    bot = {
        'version': '1.3.0', # DO NOT CHANGE
        'token': '', # BOT TOKEN (REQUIRED)
        'admin_guild_id': [000000000000000000], # ADMIN COMMAND ENABLED GUILDS (OPTIONAL)
        'wordnik_api_key': '', # WORDNIK API KEY (OPTIONAL)
    }
    settings = {
        'database_data_dir': 'database/database.sqlite',
        'command_cooldown': 5,
        'embed_color': '#249EDB',
        'embed_important_color': 'b03f58',
        'embed_success_color': '#32CD32',
        'embed_error_color': '#FF0000',
        'auto_translate_conf': 0.80,
        'auto_translate_min_relative_distance': 0.90,
    }
    economy = {
        'starting_balance': 300,
        'starting_tux_pass': 0,
        'daily_max_streak': 30,
    }
    profile = {
        'coin': {
            'gray-banner': 200,
            'float-nametag': 200,
            'separator-nametag': 200,
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
            'usa-banner': 10000,
            },
            'tpass': {
                'nippuwu-banner': 1,
            }
        }
    pokemon = {
        'pokemon_pack_amount': 7,
        'pokemon_max_capacity': 2000,
    }

    json = {
        'bot': bot,
        'settings': settings,
        'economy': economy,
        'profile': profile,
        'pokemon': pokemon,
    }
        
    return json

def update_settings():
    settings = get_setting_json()
    with open('settings.json', 'r') as openfile:
        data = json.load(openfile)
    
    for section in settings:
        if section not in data:
            data[section] = settings[section]
        else:
            for option in settings[section]:
                if option not in data[section]:
                    data[section][option] = settings[section][option]

    with open('settings.json', 'w') as openfile:
        json.dump(data, openfile, indent=4)

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

def register_user(user: hikari.User):
    db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
    cursor = db.cursor()
    
    sql = ('INSERT INTO economy(user_id, balance, total, loss, tpass, streak, date, level, experience) VALUES (?,?,?,?,?,?,?,?,?)')
    val = (user.id, get_setting('economy', 'starting_balance'), get_setting('economy', 'starting_balance'), 0, get_setting('economy', 'starting_tux_pass'), 0, None, 0, 0)
    cursor.execute(sql, val) 
    
    db.commit() # saves changes
    cursor.close()
    db.close()

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

    # Generate settings.json if not found
    if not os.path.isfile('settings.json') or not os.access('settings.json', os.R_OK): # checks if file exists
        dictionary = get_setting_json()
        
        with io.open(os.path.join('', 'settings.json'), 'w') as openfile:
            openfile.write(json.dumps(dictionary, indent=4))
        
        print('Please add your bot information to settings.json')
        sys.exit(0)
    else:
        version = get_setting('bot', 'version')
        if version != VERSION:
            write_setting('bot', 'version', VERSION)
            update_settings()

    # Check if bot token is set
    token = get_setting('bot', 'token')
    admin_guild_id = get_setting('bot', 'admin_guild_id')
    if not token:
        print('Please add your bot token to settings.json')
        sys.exit(0)

    # Create a bot instance
    bot = lightbulb.BotApp(
        token=token,
        default_enabled_guilds=admin_guild_id,
        help_class=None,
        intents=hikari.Intents.ALL,
    )

    # Create a database
    @bot.listen(hikari.StartedEvent)
    async def on_started(event):
        # Generate database directory if not found
        if not os.path.exists('database'):
            os.makedirs('database')

        db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        cursor = db.cursor() # checks if db exists
        cursor.execute('''CREATE TABLE IF NOT EXISTS economy (
            user_id INTEGER, 
            balance INTEGER,
            total INTEGER,
            loss INTEGER,
            tpass INTEGER,
            streak INTEGER,
            date TEXT
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

    # Install uvloop for Linux users
    if os.name != 'nt':
        install('uvloop')
        import uvloop
        uvloop.install()

    # Release the bot!
    tasks.load(bot)
    client = miru.Client(bot)
    bot.d.setdefault('client', client)
    bot.load_extensions_from('extensions', recursive=True)
    bot.run(
        status=hikari.Status.DO_NOT_DISTURB, 
        activity=hikari.Activity(name='Rushsite Season 4', type=hikari.ActivityType.STREAMING, url='https://www.twitch.tv/ryqb')
    )