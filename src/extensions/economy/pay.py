import hikari
import lightbulb

from bot import get_setting, verify_user, register_user
from utils.economy.manager import EconomyManager

plugin = lightbulb.Plugin('Pay')
economy = EconomyManager()

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('number', 'The number of coins', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', 'The user you are about to pay.', type=hikari.User, required=True)
@lightbulb.command('pay', 'Transfer coins to a fellow Discord member.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def pay(ctx: lightbulb.SlashContext, user: hikari.User, number: int) -> None:
    if user.is_bot or ctx.author.id == user.id: # checks if the user is a bot or the sender
        embed = hikari.Embed(description='You are not allowed to send money to this user!', color=get_setting('settings', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    
    sender = ctx.author

    if verify_user(sender) == None: # if sender has never been register
        register_user(sender)
    if verify_user(user) == None: # if user has never been register
        register_user(user)
    
    if economy.remove_money(sender.id, number, False) == False:
        embed = hikari.Embed(description='You do not have enough money!', color=get_setting('settings', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    
    economy.add_money(user.id, number, False)
    
    embed = (hikari.Embed(description=f'You sent 🪙 {number:,} to {user.global_name}!', color=get_setting('settings', 'embed_color')))
    await ctx.respond(embed)

def load(bot):
    bot.add_plugin(plugin)