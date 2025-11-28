import hikari
import lightbulb

from bot import get_setting, verify_user, register_user
from utils.economy.manager import EconomyManager

loader = lightbulb.Loader()
group = lightbulb.Group(name="tpass", description="Administer and manage user's Tux passes.", default_member_permissions=hikari.Permissions.ADMINISTRATOR)

economy = EconomyManager()

@group.register
class Set(lightbulb.SlashCommand, name="set", description="Set a guild member's passes to a specific amount."):
    user: hikari.User = lightbulb.user("user", "The user's passes that will change.")
    amount: int = lightbulb.integer("amount", "The amount that will be set to.", min_value=0, max_value=None)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        if self.user.is_bot:
            embed = hikari.Embed(description="You are not allowed to set tickets to this user!", color=get_setting("general", "embed_error_color"))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        elif verify_user(self.user) == None:
            register_user(self.user)

        economy.set_ticket(self.user.id, self.amount)
        embed = (hikari.Embed(description=f"You set {self.user.global_name}'s ticket amount to 🎟️ {self.amount:,}.", color=get_setting("general", "embed_color")))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@group.register
class Add(lightbulb.SlashCommand, name="add", description="Add passes to a guild member's wallet."):
    user: hikari.User = lightbulb.user("user", "The user's wallet that will change.")
    amount: int = lightbulb.integer("amount", "The amount that will be added to.", min_value=1, max_value=None)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        if self.user.is_bot:
            embed = hikari.Embed(description="You are not allowed to add passes to this user!", color=get_setting("general", "embed_error_color"))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        elif verify_user(self.user) == None:
            register_user(self.user)
        
        if economy.add_ticket(self.user.id, self.amount):
            embed = (hikari.Embed(description=f"You added {self.amount:,} 🎟️ to {self.user.global_name}'s wallet.", color=get_setting("general", "embed_color")))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@group.register
class Remove(lightbulb.SlashCommand, name="remove", description="Remove passes from a guild member's wallet."):
    user: hikari.User = lightbulb.user("user", "The user's passes that will change.")
    amount: int = lightbulb.integer("amount", "The amount that will be removed from.", min_value=1, max_value=None)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        if self.user.is_bot:
            embed = hikari.Embed(description="You are not allowed to remove passes to this user!", color=get_setting("general", "embed_error_color"))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        elif verify_user(self.user) == None:
            register_user(self.user)
        
        if economy.remove_ticket(self.user.id, self.amount):
            embed = (hikari.Embed(description=f"You removed {self.amount:,} 🎟️ from {self.user.global_name}'s wallet.", color=get_setting("general", "embed_color")))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        else:
            embed = (hikari.Embed(description=f"That amount exceeds {self.user.global_name}'s wallet!", color=get_setting("general", "embed_error_color")))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

loader.command(group, guilds=get_setting("bot", "test_guild_id"))