import hikari
import lightbulb

from typing import Optional
from PIL import Image

from bot import get_setting
from utils.profile.inventory import Inventory
from utils.profile.card import Card

plugin = lightbulb.Plugin('Profile')

@plugin.command
@lightbulb.option('user', 'The user to get information about.', hikari.User, required=False)
@lightbulb.command('profile', 'Retrieve information about yourself or a Discord member.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def profile(ctx: lightbulb.Context, user: Optional[hikari.Member] = None) -> None:
    user = user or ctx.member
    
    if not user:
        embed = hikari.Embed(description='That user is not in the server.', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed)
        return
    
    inventory = Inventory(user)
    profile = Card(user, ctx.bot.application)

    bg, card, nametag = inventory.get_active_customs()
    bg = Image.open(f'assets/img/general/profile/banner/{bg}.png').convert('RGBA')
    card = Image.open(f'assets/img/general/profile/base/{card}.png').convert('RGBA')
    nametag = Image.open(f'assets/img/general/profile/nametag/{nametag}.png').convert('RGBA')

    await ctx.respond(attachment=await profile.draw_card(bg, card, nametag))

def load(bot):
    bot.add_plugin(plugin)