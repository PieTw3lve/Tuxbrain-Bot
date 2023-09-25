import hikari
import lightbulb
import miru

from datetime import datetime, timezone, timedelta
from bot import DEFAULT_GUILD_ID, get_setting, write_setting

plugin = lightbulb.Plugin('Admin', default_enabled_guilds=DEFAULT_GUILD_ID)

## Admin Subcommands ##

@plugin.command
@lightbulb.app_command_permissions(perms=hikari.Permissions.ADMINISTRATOR)
@lightbulb.command('admin', 'Administer bot configurations.')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def admin(ctx: lightbulb.Context) -> None:
    return

## Announcement Command ##

@admin.child
@lightbulb.option('image', 'Announcement attachment.', type=hikari.Attachment, required=False)
@lightbulb.option('ping', 'Role to ping with announcement.', type=hikari.Role, required=True)
@lightbulb.option('channel', 'Channel to post announcement to.', type=hikari.TextableChannel, required=True)
@lightbulb.command('announce', 'Make the bot say something!', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def announce(ctx: lightbulb.Context, channel: hikari.TextableChannel, ping: hikari.Role, image: hikari.Attachment) -> None:
    modal = SayModal(channel, ping, image)
    
    await modal.send(interaction=ctx.interaction)

class SayModal(miru.Modal):
    header = miru.TextInput(label='Title', placeholder='Enter your title here!', custom_id='title', style=hikari.TextInputStyle.SHORT)
    message = miru.TextInput(label='Message', placeholder='Enter your message here!', custom_id='message', style=hikari.TextInputStyle.PARAGRAPH, min_length=1, max_length=4000, required=True)
    
    def __init__(self, channel: hikari.TextableChannel, ping: hikari.Role, image: hikari.Attachment) -> None:
        super().__init__(title='Announcement Command Prompt', custom_id='announce_command', timeout=None)
        self.channel = channel
        self.ping = ping
        self.image = image

    async def callback(self, ctx: miru.ModalContext) -> None:
        embed = hikari.Embed(title=self.header.value, description=self.message.value, color=get_setting('settings', 'embed_important_color'))
        embed.set_image(self.image)
        
        await ctx.bot.rest.create_message(content=self.ping.mention, channel=self.channel.id, embed=embed, role_mentions=True)
        
        embed = hikari.Embed(title='Success!', description=f'Announcement posted to <#{self.channel.id}>!', color=get_setting('settings', 'embed_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
## Poll Command ##

@admin.child
@lightbulb.option('timeout', 'How long should until the poll timeouts (seconds).', type=float, required=True)
@lightbulb.option('options', 'Seperate each option with a comma space.', type=str, required=True)
@lightbulb.option('image', 'Add a poll attachment!', type=hikari.Attachment, required=False)
@lightbulb.option('description', 'Description of the poll.', type=str, required=False)
@lightbulb.option('title', 'Title of the poll.', type=str, required=True)
@lightbulb.command('poll', 'Create a custom poll!', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def poll(ctx: lightbulb.Context, title: str, description: str, image: hikari.Attachment, options: str, timeout: float) -> None:
    options = list(options.split(', '))
    optionList = {}
    
    embed = hikari.Embed(
        title=title,
        description=description,
        color=get_setting('settings', 'embed_color'),
        timestamp=datetime.now().astimezone()
    )
    embed.set_image(image)
    embed.set_thumbnail('assets/img/poll.png')
    
    for option in options:
        optionList.update({option: 0})
        bar = printProgressBar(0, 1, prefix = f'👥 {optionList[option]}', suffix = '', length = 12)
        embed.add_field(name=f'{option}', value=bar, inline=False)
    
    view = PollView(embed, optionList, timeout)
    
    for option in options:
        view.add_item(PollButton(option))
    
    message = await ctx.respond(embed, components=view.build())
    await view.start(message)

class PollView(miru.View):
    def __init__(self, embed: hikari.Embed, optionList: dict, timeout: float) -> None:
        super().__init__(timeout=timeout, autodefer=True)
        self.embed = embed
        self.options = optionList
        self.voted = []

class PollButton(miru.Button):
    def __init__(self, option: str) -> None:
        super().__init__(label=option, custom_id=f'button_{option}', style=hikari.ButtonStyle.SECONDARY)
        self.option = option

    async def callback(self, ctx: miru.ViewContext) -> None:
        if ctx.user.id not in self.view.voted:
            self.view.voted.append(ctx.user.id)
            
            self.view.options[self.option] = self.view.options[self.option] + 1
            bar = printProgressBar(self.view.options[self.option], len(self.view.voted), prefix = f'👥 {self.view.options[self.option]}', suffix = '', length = 12)
            
            self.view.embed.edit_field(list(self.view.options).index(self.option), f'{self.option}', f'{bar}')
            for i in range(len(list(self.view.options))):
                if list(self.view.options)[i] != self.option:
                    bar = printProgressBar(self.view.options[list(self.view.options)[i]], len(self.view.voted), prefix = f'👥 {self.view.options[list(self.view.options)[i]]}', suffix = '', length = 12)
                    self.view.embed.edit_field(i, f'{list(self.view.options)[i]}', f'{bar}')
            
            await ctx.edit_response(self.view.embed)
            
            return
        
        embed = hikari.Embed(description='You already voted!', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def printProgressBar (iteration, total, prefix: str, suffix: str, decimals = 1, length = 100, fill = '▰', empty = '▱'):
    try:
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
    except ZeroDivisionError:
        percent = 0
        filledLength = 0
    bar = fill * filledLength + empty * (length - filledLength)
    
    return f'\r{prefix} {bar} {percent}% {suffix}'

## Set Role Command ##

@admin.child
@lightbulb.option('permission', 'The permission level to assign.', type=str, choices=['Owner', 'Admin', 'Staff', 'Rushsite S1 Winner', 'Rushsite S2 Winner', 'Rushsite S3 Winner', 'Rushsite S4 Winner', 'Rushsite S5 Winner'], required=True)
@lightbulb.option('role', 'The selected role that you want to set.', type=hikari.Role, required=True)
@lightbulb.command('set', 'Set permissions for a role.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def set_role(ctx: lightbulb.Context, role: hikari.Role, permission: str) -> None:
    match permission:
        case 'Owner':
            write_setting('roles', 'owner_role_id', role.id)
        case 'Admin':
            write_setting('roles', 'admin_role_id', role.id)
        case 'Staff':
            write_setting('roles', 'staff_role_id', role.id)
        case 'Rushsite S1 Winner':
            write_setting('roles', 'rushsite_s1_id', role.id)
        case 'Rushsite S2 Winner':
            write_setting('roles', 'rushsite_s2_id', role.id)
        case 'Rushsite S3 Winner':
            write_setting('roles', 'rushsite_s3_id', role.id)
        case 'Rushsite S4 Winner':
            write_setting('roles', 'rushsite_s4_id', role.id)
        case 'Rushsite S5 Winner':
            write_setting('roles', 'rushsite_s5_id', role.id)
    
    embed = hikari.Embed(description=f"You gave {permission} permissions to {role.mention}.", color=get_setting('settings', 'embed_color'))
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

## Close Poll Command ##

@admin.child
@lightbulb.option('message_id', 'The target poll id.', type=str, required=True)
@lightbulb.option('channel', 'The channel in which the poll is located.', type=hikari.TextableChannel, required=True)
@lightbulb.command('close-poll', 'Close an existing poll!', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def close_poll(ctx: lightbulb.Context, channel: hikari.TextableChannel, message_id: str) -> None:
    embed = hikari.Embed()
    
    try:
        await ctx.bot.rest.edit_message(channel=channel.id, message=message_id, components=[])
        embed.description = 'Successfully closed poll!'
        embed.color = get_setting('settings', 'embed_success_color')
    except:
        embed.description = 'Could not located message!'
        embed.color = get_setting('settings', 'embed_error_color')
    
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

## Purge Command ##

class PromptView(miru.View):
    async def view_check(self, ctx: miru.Context) -> bool:
        return ctx.user.id == ctx.author.id

class ConfirmButton(miru.Button):
    def __init__(self) -> None:
        super().__init__(style=hikari.ButtonStyle.DANGER, label="Confirm")
    async def callback(self, ctx: miru.Context) -> None:
        # You can access the view an item is attached to by accessing it's view property
        self.view.accepted = True
        self.view.stop()
    
class CancelButton(miru.Button):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(style=hikari.ButtonStyle.SUCCESS, label="Cancel")

    async def callback(self, ctx: miru.Context) -> None:
        self.view.accepted = False
        self.view.stop()

@admin.child
@lightbulb.option("amount", "The number of messages to purge.", type=int, required=True, max_value=1000)
@lightbulb.command("purge", "Purge messages from this channel.", aliases=["clear","prune"], pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def purge(ctx: lightbulb.Context, amount: int) -> None:
    channel = ctx.channel_id

    # If the command was invoked using the PrefixCommand, it will create a message
    # before we purge the messages, so you want to delete this message first
    if isinstance(ctx, lightbulb.PrefixContext):
        await ctx.event.message.delete()

    view = PromptView(timeout=30, autodefer=True)
    view.add_item(ConfirmButton())
    view.add_item(CancelButton())
    
    embed = hikari.Embed(title='Are you sure you want to continue the purge operation?', description='**__WARNING:__** This Action is irreversible!', color=get_setting('settings', 'embed_color'))
    message = await ctx.respond(embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)
    
    await view.start(message)
    await view.wait()

    if hasattr(view, "accepted"):
        if view.accepted is True:
            await purge_messages(ctx, amount, channel)
        elif view.accepted is False:
            await ctx.edit_last_response(hikari.Embed(title='Cancelled', description=f'Purge operation has been cancelled.', color=get_setting('settings', 'embed_error_color')), components=[])
    else:
        await ctx.edit_last_response(hikari.Embed(title='Timed out', description=f'Purge operation has been cancelled due to inactivity...', color=get_setting('settings', 'embed_error_color')), components=[])

async def purge_messages(ctx: lightbulb.Context, amount: int, channel: hikari.Snowflakeish) -> None:
    iterator = (
                ctx.bot.rest.fetch_messages(channel)
                .limit(amount)
                .take_while(lambda msg: (datetime.now(timezone.utc) - msg.created_at) < timedelta(days=14))
            )
    if iterator:
        async for messages in iterator.chunk(100):
            await ctx.bot.rest.delete_messages(channel, messages)
        await ctx.edit_last_response(hikari.Embed(title='Success', description=f'Messages has been sucessfully deleted.', color=get_setting('settings', 'embed_success_color')), components=[])
    else:
        await ctx.edit_last_response(title='Error', description=f'Could not find any messages younger than 14 days!', color=get_setting('settings', 'embed_error_color'), components=[])

## Add as a plugin ##

def load(bot):
    bot.add_plugin(plugin)