import hikari
import lightbulb
import requests
import json

from bot import get_setting

plugin = lightbulb.Plugin('Random')

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('random', 'Retrieve a random item or information.')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def rand(ctx: lightbulb.Context) -> None:
    pass

@rand.child
@lightbulb.command('fox', 'Get a random picture of a fox!')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def today_fact(ctx: lightbulb.Context) -> None:
    url = 'https://apilist.fun/out/randomfox'
    request = dict(json.loads(requests.get(url).text))
    
    await ctx.respond(request.get('image'))

@rand.child
@lightbulb.command('cat', 'Get a random picture of a cat!')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def today_fact(ctx: lightbulb.Context) -> None:
    url = 'https://api.thecatapi.com/v1/images/search'
    request = list(json.loads(requests.get(url).text))
    
    await ctx.respond(request[0].get('url'))

@rand.child
@lightbulb.command('dog', 'Get a random picture of a dog!')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def today_fact(ctx: lightbulb.Context) -> None:
    url = 'https://apilist.fun/out/randomdog'
    request = dict(json.loads(requests.get(url).text))
    
    await ctx.respond(request.get('url'))

@rand.child
@lightbulb.command('joke', 'Get a random unfunny joke!')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def joke(ctx: lightbulb.Context) -> None:
    url = 'https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit&type=twopart'
    request = dict(json.loads(requests.get(url).text))
    
    embed = hikari.Embed(title=request.get('setup'), description=f"||{request.get('delivery')}||", color=get_setting('general', 'embed_color'))
    await ctx.respond(embed)

@rand.child
@lightbulb.command('riddle', 'Get a random riddle!')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def riddle(ctx: lightbulb.Context) -> None:
    url = 'https://riddles-api.vercel.app/random'
    request = dict(json.loads(requests.get(url).text))
    
    embed = hikari.Embed(title=request.get('riddle'), description=f"||{request.get('answer')}||", color=get_setting('general', 'embed_color'))
    await ctx.respond(embed)

@rand.child
@lightbulb.command('fact', 'Get a random useless fact.')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def rand_fact(ctx: lightbulb.Context) -> None:
    url = 'https://uselessfacts.jsph.pl/random.json?language=en'
    request = dict(json.loads(requests.get(url).text))
    
    embed = hikari.Embed(title='Random Useless Fact', description=request.get('text'), color=get_setting('general', 'embed_color'))
    await ctx.respond(embed)

def load(bot):
    bot.add_plugin(plugin)