import hikari
import lightbulb
import miru

from datetime import datetime, timezone, timedelta
from bot import get_setting

plugin = lightbulb.Plugin('Purge')

class PromptView(miru.View):
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == ctx.author.id

class ConfirmButton(miru.Button):
    def __init__(self) -> None:
        super().__init__(style=hikari.ButtonStyle.DANGER, label="Confirm")
    async def callback(self, ctx: miru.ViewContext) -> None:
        # You can access the view an item is attached to by accessing it's view property
        self.view.accepted = True
        self.view.stop()
    
class CancelButton(miru.Button):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(style=hikari.ButtonStyle.SUCCESS, label="Cancel")

    async def callback(self, ctx: miru.ViewContext) -> None:
        self.view.accepted = False
        self.view.stop()

@plugin.command
@lightbulb.app_command_permissions(perms=hikari.Permissions.MANAGE_MESSAGES, dm_enabled=False)
@lightbulb.option('amount', 'The number of messages to purge.', type=int, required=True, max_value=1000)
@lightbulb.command('purge', 'Remove messages from a Discord channel.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def purge(ctx: lightbulb.Context, amount: int) -> None:
    channel = ctx.channel_id

    # If the command was invoked using the PrefixCommand, it will create a message
    # before we purge the messages, so you want to delete this message first
    if isinstance(ctx, lightbulb.PrefixContext):
        await ctx.event.message.delete()

    view = PromptView(timeout=30, autodefer=True)
    view.add_item(ConfirmButton())
    view.add_item(CancelButton())
    
    embed = hikari.Embed(title='Are you sure you want to continue the purge operation?', description='**__WARNING:__** This Action is irreversible!', color=get_setting('general', 'embed_color'))
    await ctx.respond(embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)
    
    client = ctx.bot.d.get('client')
    client.start_view(view)
    await view.wait()

    if hasattr(view, 'accepted'):
        if view.accepted is True:
            await purge_messages(ctx, amount, channel)
        elif view.accepted is False:
            await ctx.edit_last_response(hikari.Embed(title='Cancelled', description=f'Purge operation has been cancelled.', color=get_setting('general', 'embed_error_color')), components=[])
    else:
        await ctx.edit_last_response(hikari.Embed(title='Timed out', description=f'Purge operation has been cancelled due to inactivity...', color=get_setting('general', 'embed_error_color')), components=[])

async def purge_messages(ctx: lightbulb.Context, amount: int, channel: hikari.Snowflakeish) -> None:
    iterator = (
                ctx.bot.rest.fetch_messages(channel)
                .limit(amount)
                .take_while(lambda msg: (datetime.now(timezone.utc) - msg.created_at) < timedelta(days=14))
            )
    if iterator:
        async for messages in iterator.chunk(100):
            await ctx.bot.rest.delete_messages(channel, messages)
        await ctx.edit_last_response(hikari.Embed(title='Success', description=f'Messages has been successfully deleted.', color=get_setting('general', 'embed_success_color')), components=[])
    else:
        await ctx.edit_last_response(title='Error', description=f'Could not find any messages younger than 14 days!', color=get_setting('general', 'embed_error_color'), components=[])

def load(bot):
    bot.add_plugin(plugin)