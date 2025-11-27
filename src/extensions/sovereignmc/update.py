import hikari
import lightbulb

from datetime import datetime

from .convert import GUILD_ID
from utils.economy.sovereignmc import SovManager

loader = lightbulb.Loader()

database = SovManager()

def check_day() -> None:
    today = datetime.now().strftime("%A")

    if today == "Monday":
        database.reset_database()

@loader.task(lightbulb.crontrigger("0 5 * * *"), auto_start=False)
async def task():
    check_day()

@loader.listener(hikari.StartedEvent)
async def on_start(event: hikari.StartedEvent, bot: hikari.GatewayBot, client: lightbulb.Client) -> None:
    try:
        guild = await bot.rest.fetch_guild(GUILD_ID)
        if guild is not None:
            task.start()
            check_day()
    except:
        await loader.remove_from_client(client)