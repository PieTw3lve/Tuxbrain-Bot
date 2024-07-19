from typing import Literal
import hikari
import lightbulb
import miru

from bot import get_setting

plugin = lightbulb.Plugin('Broadcast')

class SayModal(miru.Modal):
    header = miru.TextInput(label='Title', placeholder='Enter your title here.', custom_id='title', style=hikari.TextInputStyle.SHORT)
    message = miru.TextInput(label='Message', placeholder='Enter your message here.', custom_id='message', style=hikari.TextInputStyle.PARAGRAPH, min_length=1, max_length=4000, required=True)
    
    def __init__(self, channel: hikari.TextableChannel, ping: hikari.Role, image: hikari.Attachment) -> None:
        super().__init__(title='Announcement Command Prompt', custom_id='announce_command', timeout=None)
        self.channel = channel
        self.ping = ping
        self.image = image

    async def callback(self, ctx: miru.ModalContext) -> None:
        embed = hikari.Embed(title=self.header.value, description=self.message.value, color=get_setting('general', 'embed_important_color'))
        embed.set_image(self.image)
        
        await ctx.bot.rest.create_message(content=self.ping.mention, channel=self.channel.id, embed=embed, role_mentions=True)
        
        embed = hikari.Embed(title='Success!', description=f'Announcement posted to <#{self.channel.id}>!', color=get_setting('general', 'embed_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@plugin.command
@lightbulb.app_command_permissions(perms=hikari.Permissions.MANAGE_CHANNELS, dm_enabled=False)
@lightbulb.option('image', 'Announcement attachment.', type=hikari.Attachment, required=False)
@lightbulb.option('ping', 'Role to ping with announcement.', type=hikari.Role, required=True)
@lightbulb.option('channel', 'Channel to post announcement to.', type=hikari.TextableChannel, required=True)
@lightbulb.command('broadcast', 'Command the bot to deliver a message.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def broadcast(ctx: lightbulb.Context, channel: hikari.TextableChannel, ping: hikari.Role, image: hikari.Attachment) -> None:
    modal = SayModal(channel, ping, image)
    
    await modal.send(interaction=ctx.interaction)

def load(bot):
    bot.add_plugin(plugin)