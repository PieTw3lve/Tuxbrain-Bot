import hikari
import lightbulb
import requests
import json

from bot import get_setting

plugin = lightbulb.Plugin('Bored')

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('bored', 'Receive a suggested activity from the bot.')
@lightbulb.implements(lightbulb.SlashCommand)
async def bored(ctx: lightbulb.Context) -> None:
    url = 'https://www.boredapi.com/api/activity'
    request = dict(json.loads(requests.get(url).text))
    
    embed = hikari.Embed(title=f"{request.get('activity')}.", description=f"Type: {request.get('type').capitalize()}\nParticipants: {request.get('participants')}\n Price: 🪙 {request.get('price'):,}\nAccessibility: {request.get('accessibility')}", color=get_setting('settings', 'embed_color'))
    await ctx.respond(embed)

def load(bot):
    bot.add_plugin(plugin)