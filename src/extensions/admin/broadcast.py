import asyncio
from typing import Literal
import uuid
import hikari
import lightbulb

from bot import get_setting

loader = lightbulb.Loader()

class SayModal(lightbulb.components.Modal):
    def __init__(self, channel: hikari.TextableChannel, ping: hikari.Role, image: hikari.Attachment) -> None:
        self.header = self.add_short_text_input(label="Title", placeholder="Enter your title here...", required=False)
        self.message = self.add_paragraph_text_input(label="Message", placeholder="Enter your message here...", min_length=1, max_length=4000, required=True)
        self.channel = channel
        self.ping = ping
        self.image = image

    async def on_submit(self, ctx: lightbulb.components.ModalContext) -> None:
        embed = hikari.Embed(title=ctx.value_for(self.header), description=ctx.value_for(self.message), color=get_setting('general', 'embed_important_color'))
        embed.set_image(self.image)
        
        if self.ping:
            await ctx.client.rest.create_message(content=self.ping.mention, channel=self.channel.id, embed=embed, role_mentions=True)
        else:
            await ctx.client.rest.create_message(channel=self.channel.id, embed=embed)

        embed = hikari.Embed(title='Success!', description=f'Announcement posted to <#{self.channel.id}>!', color=get_setting('general', 'embed_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@loader.command
class BroadcastCommand(lightbulb.SlashCommand, name="broadcast", description="Command the bot to deliver a message.", default_member_permissions=hikari.Permissions.MANAGE_CHANNELS):
    channel: hikari.TextableChannel = lightbulb.channel("channel", "Channel to post announcement to.")
    ping: hikari.Role = lightbulb.role("ping", "Role to ping with announcement.", default=None)
    image: hikari.Attachment = lightbulb.attachment("image", "Announcement attachment.", default=None)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        modal = SayModal(self.channel, self.ping, self.image)

        await ctx.respond_with_modal("Announcement Prompt", cid := str(uuid.uuid4()), components=modal)

        try:
            await modal.attach(ctx.client, cid, timeout=3600)
        except asyncio.TimeoutError:
            pass