import hikari
import lightbulb

from lightbulb.ext import tasks
from lightbulb.ext.tasks import CronTrigger
from datetime import datetime

from .convert import GUILD_ID
from utils.economy.sovereignmc import SovManager

plugin = lightbulb.Plugin('SovereignMCReset')
database = SovManager()

@tasks.task(CronTrigger('0 5 * * *'), auto_start=False)
def check_day() -> None:
    today = datetime.now().strftime('%A')

    if today == 'Monday':
        database.reset_database()

@plugin.listener(hikari.StartedEvent)
async def on_start(event: hikari.StartedEvent) -> None:
    if plugin.bot.cache.get_guild(GUILD_ID) is not None:
        check_day.start()
        check_day()
    else:
        plugin.bot.remove_plugin(plugin)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)