import asyncio
import os
import json
import io
import subprocess
import sys
import hikari
import lightbulb
import sqlite3

import extensions

from utils.general.config import VERSION, get_setting_json, update_settings, get_setting, write_setting

## Functions ##

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def register_user(user: hikari.User):
    db = sqlite3.connect(get_setting("general", "database_data_dir"))
    cursor = db.cursor()
    
    sql = ("INSERT INTO economy(user_id, balance, total, loss, tpass, streak, date) VALUES (?,?,?,?,?,?,?)")
    val = (user.id, get_setting("economy", "starting_balance"), get_setting("economy", "starting_balance"), 0, get_setting("economy", "starting_tux_pass"), 0, None)
    cursor.execute(sql, val) 
    
    db.commit() # saves changes
    cursor.close()
    db.close()

def verify_user(user: hikari.User):
    db = sqlite3.connect(get_setting("general", "database_data_dir"))
    cursor = db.cursor()
    
    cursor.execute(f"SELECT user_id FROM economy WHERE user_id = {user.id}") # moves cursor to user"s id from database
    result = cursor.fetchone() # grabs the value of user"s id
    
    return result

## Script ##

if __name__ == "__main__":
    # Generate settings.json if not found
    settingsFile  = "settings.json"
    if not os.path.isfile(settingsFile) or not os.access(settingsFile, os.R_OK):
        settings = get_setting_json()
        with io.open(settingsFile, "w") as file:
            file.write(json.dumps(settings, indent=4))
        print("Please add your bot information to settings.json")
        sys.exit(0)
    
    version = get_setting("bot", "version")
    if version != VERSION:
        write_setting("bot", "version", VERSION)
        update_settings()

    # Check if bot token is set
    token = get_setting("bot", "token")
    if not token:
        print("Please add your bot information to settings.json")
        sys.exit(0)

    # Create a bot instance
    bot = hikari.GatewayBot(
        token=token,
        intents=hikari.Intents.ALL,
    )
    client: lightbulb.Client = lightbulb.client_from_app(
        app=bot,
        default_enabled_guilds=get_setting("bot", "test_guild_id"),
    )

    registry = client.di.registry_for(lightbulb.di.Contexts.DEFAULT)
    # registry.register_value(lightbulb.Client, client)

    # Create a database
    @bot.listen(hikari.StartingEvent)
    async def on_starting(_: hikari.StartingEvent) -> None:
        # Generate database directory if not found
        if not os.path.exists("database"):
            os.makedirs("database")
        
        db = sqlite3.connect(get_setting("general", "database_data_dir"))
        cursor = db.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS economy (
            user_id INTEGER, 
            balance INTEGER,
            total INTEGER,
            loss INTEGER,
            tpass INTEGER,
            streak INTEGER,
            date TEXT
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS profile (
            user_id TEXT,
            name TEXT, 
            type TEXT,
            active INTEGER,
            PRIMARY KEY (user_id, type, name)
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS fishing (
            user_id TEXT,
            bait_id TEXT,
            amount INTEGER,
            PRIMARY KEY (user_id, bait_id)
        )""")

        # Load the commands
        await client.load_extensions_from_package(extensions, recursive=True)
        # Start the client - causing the commands to be synced with discord
        await client.start()

    # Install uvloop for Linux users
    if os.name != "nt":
        install("uvloop")
        import uvloop
        uvloop.install()
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    # Release the bot!
    bot.run(
        status=hikari.Status.DO_NOT_DISTURB, 
        activity=hikari.Activity(
            name="Rushsite Season 4", 
            type=hikari.ActivityType.STREAMING, 
            url="https://www.twitch.tv/ryqb"
        ),
        propagate_interrupts=False, 
    )