import hikari
import lightbulb

from miru.ext import nav
from typing import Optional

from bot import get_setting
from utils.economy.manager import EconomyManager
from utils.pokemon.inventory import Inventory, SellView, NavPageInfo

plugin = lightbulb.Plugin('Pokeinv')
economy = EconomyManager()

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('pokeinv', 'Organize your Pokémon cards and packs inventory.')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def inventory(ctx: lightbulb.Context) -> None:
    return

## Inventory View Command ##

@inventory.child
@lightbulb.option('user', 'The user to get information about.', type=hikari.User, required=False)
@lightbulb.command('view', "Open a server member's pack inventory.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def open(ctx: lightbulb.Context, user: Optional[hikari.User] = None) -> None:
    if not (guild := ctx.get_guild()):
        embed = hikari.Embed(description='This command may only be used in servers.', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed)
        return
    elif user != None and user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description="You are not allowed to view this user's inventory!", color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return

    user = user or ctx.author
    user = ctx.bot.cache.get_member(guild, user)
    
    if not user:
        embed = hikari.Embed(description='That user is not in the server.', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed)
        return
    
    inventory = Inventory(ctx, user)
    pages = inventory.show_inventory(10)
    buttons = [nav.FirstButton(row=1), nav.PrevButton(emoji='⬅️', row=1), NavPageInfo(len(pages), 1), nav.NextButton(emoji='➡️', row=1), nav.LastButton(row=1)]
    navigator = nav.NavigatorView(pages=pages, buttons=buttons, timeout=None)

    await navigator.send(ctx.interaction)

## Sell Command ##

@inventory.child
@lightbulb.command('sell', "Sell your cards.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def sell(ctx: lightbulb.Context) -> None:
    inventory = Inventory(ctx, ctx.author)
    embed = hikari.Embed(title='Sell Menu', description='Favorited cards will **not** be accounted for in the algorithm. \nIn the future, additional selling options may become available. \n\n> Normal = 🪙 20 \n> Shiny = 🪙 40 \n‍', color=get_setting('settings', 'embed_error_color'))
    embed.set_thumbnail('assets/img/pokemon/convert_icon.png')
    embed.set_footer(text='Once you sell cards, the action cannot be undone.')
    view = SellView(embed, inventory)
    message = await ctx.respond(embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL) 

    await view.start(message)

def load(bot):
    bot.add_plugin(plugin)