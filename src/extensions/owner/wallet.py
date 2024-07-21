import hikari
import lightbulb

from bot import get_setting, verify_user, register_user
from utils.economy.manager import EconomyManager

plugin = lightbulb.Plugin('Wallet')
economy = EconomyManager()

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command('wallet', "Administer and manage user's coins.")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def wallet(ctx: lightbulb.Context) -> None:
    return

@wallet.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option('amount', 'The amount that will be set to.', type=int, min_value=0, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('set', "Set a server member's wallet to a specific amount.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def set_wallet(ctx: lightbulb.Context, user: hikari.User, currency: str, amount: int):
    if user.is_bot:
        embed = hikari.Embed(description='You are not allowed to set money to this user!', color=get_setting('general', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None:
        register_user(ctx.user)

    economy.set_money(user.id, amount)
    embed = (hikari.Embed(description=f"You set {user.global_name}'s money to 🪙 {amount:,}.", color=get_setting('general', 'embed_color')))
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@wallet.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option('update', 'This will update net gain.', type=bool, required=True)
@lightbulb.option('amount', 'The amount that will be added to.', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('add', "Add coins to a server member's wallet.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def add(ctx: lightbulb.Context, user: hikari.User, amount: int, update: bool):
    if user.is_bot:
        embed = hikari.Embed(description='You are not allowed to add money to this user!', color=get_setting('general', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None:
        register_user(ctx.user)
    
    if economy.add_money(user.id, amount, update):
        embed = (hikari.Embed(description=f"You added 🪙 {amount:,} to {user.global_name}'s wallet.", color=get_setting('general', 'embed_color')))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@wallet.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option('update', 'This will update net loss.', type=bool, required=True)
@lightbulb.option('amount', 'The amount that will be removed from.', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('remove', "Remove coins from a server member's wallet.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def remove(ctx: lightbulb.Context, user: hikari.User, amount: int, update: bool):
    if user.is_bot:
        embed = hikari.Embed(description='You are not allowed to take money from this user!', color=get_setting('general', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None:
        register_user(ctx.user)
    
    if economy.remove_money(user.id, amount, update):
        embed = (hikari.Embed(description=f"You took 🪙 {amount:,} from {user.global_name}'s wallet.", color=get_setting('general', 'embed_color')))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    else:
        embed = (hikari.Embed(description=f"That amount exceeds {user.global_name}'s wallet!", color=get_setting('general', 'embed_error_color')))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def load(bot):
    bot.add_plugin(plugin)