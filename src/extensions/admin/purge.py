import asyncio
import hikari
import lightbulb

from datetime import datetime, timezone, timedelta
from bot import get_setting

loader = lightbulb.Loader()

class PurgeMenu(lightbulb.components.Menu):
    def __init__(self) -> None:
        self.confirmButton = self.add_interactive_button(style=hikari.ButtonStyle.DANGER, label="Confirm", on_press=self.on_confirm)
        self.cancelButton = self.add_interactive_button(style=hikari.ButtonStyle.SUCCESS, label="Cancel", on_press=self.on_cancel)
        self.accepted = False

    async def on_confirm(self, ctx: lightbulb.components.MenuContext) -> None:
        self.accepted = True
        ctx.stop_interacting()

    async def on_cancel(self, ctx: lightbulb.components.MenuContext) -> None:
        ctx.stop_interacting()

    async def predicate(self, ctx: lightbulb.components.MenuContext) -> bool:
        return True

@loader.command
class Purge(lightbulb.SlashCommand, name="purge", description="Remove messages from a Discord channel.", default_member_permissions=hikari.Permissions.MANAGE_MESSAGES):
    messages: int = lightbulb.integer("messages", "The number of messages to purge.", max_value=1000)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, bot: hikari.GatewayBot) -> None:
        channel = ctx.channel_id

        menu = PurgeMenu()
        
        embed = hikari.Embed(title="Are you sure you want to continue the purge operation?", description="**__WARNING:__** This Action is irreversible!", color=get_setting("general", "embed_color"))
        
        resp = await ctx.respond(embed, components=menu, flags=hikari.MessageFlag.EPHEMERAL)

        try:
            await menu.attach(ctx.client, timeout=30)
        except asyncio.TimeoutError:
            await ctx.edit_response(resp, components=[])

        if menu.accepted:
            await purge_messages(ctx, bot, resp, self.messages, channel)
        else:
            await ctx.edit_response(resp, hikari.Embed(title="Cancelled", description="Purge operation has been cancelled.", color=get_setting("general", "embed_error_color")), components=[])

async def purge_messages(ctx: lightbulb.Context, bot: hikari.GatewayBot, resp: int, amount: int, channel: hikari.Snowflakeish) -> None:
    iterator = (
                bot.rest.fetch_messages(channel)
                .limit(amount)
                .take_while(lambda msg: (datetime.now(timezone.utc) - msg.created_at) < timedelta(days=14))
            )
    if iterator:
        async for messages in iterator.chunk(100):
            await bot.rest.delete_messages(channel, messages)
        await ctx.edit_response(resp, hikari.Embed(title="Success", description=f"Messages has been successfully deleted.", color=get_setting("general", "embed_success_color")), components=[])
    else:
        await ctx.edit_response(resp, hikari.Embed(title="Error", description=f"Could not find any messages younger than 14 days!", color=get_setting("general", "embed_error_color")), components=[])