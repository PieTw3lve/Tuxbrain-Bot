import hikari
import lightbulb
import miru

from datetime import datetime
from bot import get_setting

plugin = lightbulb.Plugin('Open Poll')

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

@plugin.command
@lightbulb.app_command_permissions(perms=hikari.Permissions.MANAGE_CHANNELS, dm_enabled=False)
@lightbulb.option('timeout', 'How long should until the poll timeouts (seconds).', type=float, required=True)
@lightbulb.option('options', 'Seperate each option with a comma space.', type=str, required=True)
@lightbulb.option('image', 'Add a poll attachment!', type=hikari.Attachment, required=False)
@lightbulb.option('description', 'Description of the poll.', type=str, required=False)
@lightbulb.option('title', 'Title of the poll.', type=str, required=True)
@lightbulb.command('poll', 'Create a customizable poll.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
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
    embed.set_thumbnail('assets/img/fun/poll.png')
    
    for option in options:
        optionList.update({option: 0})
        bar = printProgressBar(0, 1, prefix = f'👥 {optionList[option]}', suffix = '', length = 12)
        embed.add_field(name=f'{option}', value=bar, inline=False)
    
    view = PollView(embed, optionList, timeout)
    
    for option in options:
        view.add_item(PollButton(option))
    
    message = await ctx.respond(embed, components=view.build())
    await view.start(message)

def printProgressBar (iteration, total, prefix: str, suffix: str, decimals = 1, length = 100, fill = '▰', empty = '▱'):
    try:
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
    except ZeroDivisionError:
        percent = 0
        filledLength = 0
    bar = fill * filledLength + empty * (length - filledLength)
    
    return f'\r{prefix} {bar} {percent}% {suffix}'

def load(bot):
    bot.add_plugin(plugin)