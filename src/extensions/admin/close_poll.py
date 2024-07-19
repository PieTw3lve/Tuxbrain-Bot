import hikari
import lightbulb

from bot import get_setting

plugin = lightbulb.Plugin('Close Poll')

@plugin.command
@lightbulb.app_command_permissions(perms=hikari.Permissions.MANAGE_CHANNELS, dm_enabled=False)
@lightbulb.option('message_id', 'The target poll id.', type=str, required=True)
@lightbulb.option('channel', 'The channel in which the poll is located.', type=hikari.TextableChannel, required=True)
@lightbulb.command('close-poll', 'End an ongoing poll.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def close_poll(ctx: lightbulb.Context, channel: hikari.TextableChannel, message_id: str) -> None:
    embed = hikari.Embed()
    
    try:
        await ctx.bot.rest.edit_message(channel=channel.id, message=message_id, components=[])
        embed.description = 'Successfully closed poll!'
        embed.color = get_setting('general', 'embed_success_color')
    except:
        embed.description = 'Could not located message!'
        embed.color = get_setting('general', 'embed_error_color')
    
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def load(bot):
    bot.add_plugin(plugin)