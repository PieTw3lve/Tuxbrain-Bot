import hikari
import lightbulb
import requests
import json

from bot import get_setting

plugin = lightbulb.Plugin('Fact')

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('fact', 'Discover the daily trivia.')
@lightbulb.implements(lightbulb.SlashCommand)
async def today_fact(ctx: lightbulb.Context) -> None:
    url = 'https://uselessfacts.jsph.pl/today.json?language=en'
    request = dict(json.loads(requests.get(url).text))
    
    embed = hikari.Embed(title='Useless Fact of the Day!', description=request.get('text'), color=get_setting('settings', 'embed_color'))
    await ctx.respond(embed)

def load(bot):
    bot.add_plugin(plugin)