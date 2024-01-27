import hikari
import lightbulb

from bot import get_setting

plugin = lightbulb.Plugin('Ping')

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('ping', "Check the bot's latency.")
@lightbulb.implements(lightbulb.SlashCommand)
async def ping(ctx: lightbulb.Context) -> None:
    embed = (hikari.Embed(title='Pong!', description=f'{round(ctx.bot.heartbeat_latency * 1000)}ms 📶', color=get_setting('settings', 'embed_color')))
    await ctx.respond(embed)

def load(bot):
    bot.add_plugin(plugin)