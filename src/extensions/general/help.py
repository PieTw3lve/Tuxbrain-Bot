import hikari
import lightbulb
import miru

from miru.ext import nav
from bot import VERSION, get_setting, get_commands
from utils.pokemon.inventory import NavPageInfo

plugin = lightbulb.Plugin('Help')

class InfoView(miru.View):
    def __init__(self, commands: dict) -> None:
        super().__init__(timeout=None, autodefer=False)
        self.commands = commands
    
    @miru.text_select(
        custom_id='info_select',
        placeholder='Choose a category',
        options=[
            miru.SelectOption(label='About', emoji='💬', value='About', description='More info about Tuxbrain Bot.'),
            miru.SelectOption(label='Invite Bot', emoji='🤖', value='Invite', description='How do I invite Tuxbrain Bot to my server?'),
            miru.SelectOption(label='Commands', emoji='📝', value='Commands', description='Explore an array of versatile and essential commands.'),
        ]
    )
    async def select_menu(self, select: miru.TextSelect, ctx: miru.Context) -> None:
        option = select.values[0]
          
        match option:
            case 'About':
                embed = hikari.Embed(color=get_setting('settings', 'embed_color')) 
                author = await ctx.bot.rest.fetch_user('291001658362560513')
                embed.title = '💬 About'
                embed.description = f'Tuxbrain Bot is an [open source](https://github.com/PieTw3lve/Tux_Bot), multi-use Discord bot written in [hikari.py](https://www.hikari-py.dev/), a new static-typed Python API wrapper. It is programmed by <@{author.id}> to serve as the official Tuxbrain.org Discord bot. The bot is currently still in development, so there may be some bugs. Although it was designed for Tuxbrain.org servers, the bot can be hosted and used on any server.'
                embed.set_thumbnail(author.avatar_url)
                embed.add_field(name='Additional sources:', value='Profile and Rushsite designs - <@265992381780721675>\nRushsite data - <@353620712436531205>', inline=False)
                embed.add_field(name='Find any bugs?', value='If any bugs are encountered, please submit them on [Github](https://github.com/PieTw3lve/Tuxbrain-Bot/issues).', inline=False)
                return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            case 'Invite':
                embed = hikari.Embed(color=get_setting('settings', 'embed_color')) 
                embed.title = '🤖 Invite Bot'
                embed.description = 'Tuxbrain Bot is not currently available for direct invite to personal servers, but can be hosted locally by downloading from [Github](https://github.com/PieTw3lve/Tux_Bot). Instructions for hosting Tuxbrain Bot can be found on the GitHub repository.'
                return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            case 'Commands':
                names = sorted([name for category in self.commands.values() for name, description in category])
                commands = [lightbulb.BotApp.get_slash_command(self=plugin.bot, name=name) for name in names]
                pages = self.generate_pages(commands, 8)
                buttons = [nav.PrevButton(emoji='⬅️', row=1), NavPageInfo(len(pages), 1), nav.NextButton(emoji='➡️', row=1)]
                navigator = nav.NavigatorView(pages=pages, buttons=buttons, timeout=None)
                return await navigator.send(ctx.interaction, ephemeral=True)
    
    def generate_pages(self, commands: list[lightbulb.SlashCommand | None], items_per_page: int) -> list:
        pages = []
        for i in range(0, len(commands), items_per_page):
            embed = hikari.Embed(title='📝 List of Commands', description='Certain commands may not be **selectable** due to the presence of **subcommands**.\n', color=get_setting('settings', 'embed_color'))
            embed.set_footer('Select a command by clicking on it to execute.')
            end = i + items_per_page
            for command in commands[i:end]:
                commandID = [command.id for command in command.instances.values()][0]
                embed.description += f'\n</{command.name}:{commandID}>\n ⤷ {command.description}'
            pages.append(embed)
        return pages

    async def view_check(self, ctx: miru.Context) -> bool:
        return True

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('help', 'Access additional information and commands.')
@lightbulb.implements(lightbulb.SlashCommand)
async def help(ctx: lightbulb.Context) -> None:
    bot = await ctx.bot.rest.fetch_user('1045533498481577984')
    view = InfoView(get_commands(plugin.bot))
    
    embed = (hikari.Embed(title=f'Tuxbrain Bot  `v{VERSION}`', description='I am a simple and humble bot that can do really cool things!', color=get_setting('settings', 'embed_color'))
        .set_thumbnail(bot.avatar_url)
        .add_field('I have various cool features:', '• Profile Customization\n• Economy Integration\n• Music Player\n• Pokémon Card Gacha and Trading\n• Moderation\n• Fun Interactive Games\n• And Many More!', inline=True)
        .add_field('Want to learn more about Tuxbrain Bot?', '\n\nClick on 💬 **About** to learn more about Tuxbrain Bot!\n\n**Want to learn more about commands?**\nAll commands are located in the dropdown menu.', inline=True)
        .set_footer('Use the select menu below for more info!')
    )
    
    message = await ctx.respond(embed, components=view.build())

    await view.start(message)

def load(bot):
    bot.add_plugin(plugin)