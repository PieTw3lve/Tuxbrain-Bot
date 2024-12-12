import hikari
import lightbulb

from lightbulb.ext import tasks
from lightbulb.ext.tasks import CronTrigger
from datetime import datetime

from .convert import GUILD_ID
from utils.economy.sovereignmc import SovManager

plugin = lightbulb.Plugin('SovereignMCReset')
database = SovManager()

def check_day() -> None:
    today = datetime.now().strftime('%A')

    if today == 'Monday':
        database.reset_database()

def load(bot: lightbulb.BotApp) -> None:
    if bot.cache.get_guild(GUILD_ID) is not None:
        bot.add_plugin(plugin)
        tasks.Task(check_day, CronTrigger('0 5 * * *'), True, 3, None, False, hikari.UNDEFINED).start()
        check_day()