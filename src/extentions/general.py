import hikari
import lightbulb
import miru

from datetime import datetime
from typing import Optional
from bot import VERSION, get_setting, get_commands

plugin = lightbulb.Plugin('General')

## Help Command ##

class InfoView(miru.View):
    def __init__(self, commands: dict) -> None:
        super().__init__(timeout=None)
        self.commands = commands
    
    @miru.text_select(
        custom_id='info_select',
        placeholder='Choose a category',
        options=[
            miru.SelectOption(label='About', emoji='💬', value='About', description='More info about Tux Bot.'),
            miru.SelectOption(label='Invite Bot', emoji='🤖', value='Invite', description='How do I invite Tux Bot to my server?'),
            miru.SelectOption(label='General Commands', emoji='📝', value='General', description='Explore an array of versatile and essential commands.'),
            miru.SelectOption(label='Economy Commands', emoji='💰', value='Economy', description='Strategize, amass wealth, become the richest.'),
            miru.SelectOption(label='Pokémon Commands', emoji='<:standard_booster_pack:1073771426324156428>', value='Pokemon', description='Embark on a journey of collecting and trading Pokémon.'),
            miru.SelectOption(label='Fun Commands', emoji='🎲', value='Fun', description='Play fun interactive games with users.'),
        ]
    )
    async def select_menu(self, select: miru.TextSelect, ctx: miru.Context) -> None:
        option = select.values[0]
        commands = []
        description = []
        
        embed = hikari.Embed(color=get_setting('embed_color'))   
        match option:
            case 'About':
                author = await ctx.bot.rest.fetch_user('291001658362560513')
                embed.title = '💬 About'
                embed.description = 'Tux Bot is an [open source](https://github.com/PieTw3lve/Tux_Bot), multi-use Discord bot written in [hikari.py](https://www.hikari-py.dev/), a new static-typed Python API. It was programmed by **Pie12#1069** and is currently in alpha, so there may be some bugs. Although it was designed for the Tux servers, it can also be used for personal use. However, please make sure to check the license before using it. \n\nIf you find any bugs, please mention or private message **Pie12#1069** on Discord.'
                embed.set_thumbnail(author.avatar_url)
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
            case 'Invite':
                embed.title = '🤖 Invite Bot'
                embed.description = 'Tux Bot is not currently available for direct invite to personal servers, but can be hosted locally by downloading from [Github](https://github.com/PieTw3lve/Tux_Bot). Instructions for hosting Tux Bot can be found on the GitHub repository.'
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
            case 'General':
                embed.title = '📝 General Commands'
                sections = ['General', 'Music', 'Rushsite', 'Admin']
            case 'Economy':
                embed.title = '💰 Economy Commands'
                sections = ['Economy']
            case 'Pokemon':
                embed.title = '<:pokecoin:1073778162196025484> Pokémon Commands'
                sections = ['Pokemon']
            case 'Fun':
                embed.title = '🎲 Fun Commands'
                sections = ['Fun']
        
        for section in sections:
            for cmd, desc in self.commands[section]:
                commands.append(f'• {cmd.capitalize()}')
                description.append(f'{desc}')
        
        embed.add_field('Commands', '\n'.join(commands) if len(commands) > 0 else 'None', inline=True)
        embed.add_field('Description', '\n'.join(description) if len(description) > 0 else 'None', inline=True)
        embed.set_footer('Some commands have subcommands or aliases.')
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
    async def view_check(self, context: miru.Context) -> bool:
        return True

@plugin.command
@lightbulb.command('help', 'Displays the help menu.')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def help(ctx: lightbulb.Context) -> None:
    bot = await ctx.bot.rest.fetch_user('1045533498481577984')
    view = InfoView(get_commands(plugin.bot))
    
    embed = (hikari.Embed(title=f'Tux Bot  `v{VERSION}`', description='I am a simple and humble bot that can do really cool things!', color=get_setting('embed_color'))
        .set_thumbnail(bot.avatar_url)
        .add_field('I have various cool features:', '• Economy Integration\n• Customizable Music Player\n• Pokémon Gotcha\n• Fun Interactive Games\n• And Many More!', inline=True)
        .add_field('Want to learn more about Tux Bot?', 'Click on 💬 **About** to learn more about Tux Bot! \n\nShoutouts to **Ryan#3388** and **BoboTheChimp#6164** for helping!', inline=True)
        .set_footer('Use the select menu below for more info!')
    )
    
    message = await ctx.respond(embed, components=view.build())

    await view.start(message)

## Ping Command ##

@plugin.command
@lightbulb.add_cooldown(length=10.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.command('ping', "Displays bot's latency.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def ping(ctx: lightbulb.Context) -> None:
    embed = (hikari.Embed(title='Pong!', description=f'{round(ctx.bot.heartbeat_latency * 1000)}ms 📶', color=get_setting('embed_color')))
    await ctx.respond(embed)

## Profile Command ##

@plugin.command
@lightbulb.add_cooldown(length=10.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.option('user', 'The user to get information about.', hikari.User, required=False)
@lightbulb.command('profile', 'Get info on a server member.', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def profile(ctx: lightbulb.Context, user: Optional[hikari.User] = None) -> None:
    if not (guild := ctx.get_guild()):
        embed = hikari.Embed(description='This command may only be used in servers.', color=get_setting('embed_error_color'))
        await ctx.respond(embed)
        return

    user = user or ctx.author
    user = ctx.bot.cache.get_member(guild, user)
    
    if not user:
        embed = hikari.Embed(description='That user is not in the server.', color=get_setting('embed_error_color'))
        await ctx.respond(embed)
        return
    
    created_at = int(user.created_at.timestamp())
    joined_at = int(user.joined_at.timestamp())
    
    roles = (await user.fetch_roles())[1:]  # All but @everyone
    roles = sorted(roles, key=lambda role: role.position, reverse=True)  # sort them by position, then reverse the order to go from top role down

    embed = (
        hikari.Embed(title=f'User Info - {user.display_name}', description=f'ID: `{user.id}`', color=get_setting('embed_color'), timestamp=datetime.now().astimezone())
        .set_footer(text=f'Requested by {ctx.author.username}', icon=ctx.author.display_avatar_url)
        .set_thumbnail(user.avatar_url if user.avatar_url != None else user.default_avatar_url)
        .add_field('Bot?', 'Yes' if user.is_bot else 'No', inline=True)
        .add_field('Created account on', f'<t:{created_at}:d>\n(<t:{created_at}:R>)', inline=True)
        .add_field('Joined server on', f'<t:{joined_at}:d>\n(<t:{joined_at}:R>)', inline=True)
        .add_field('Roles', ', '.join(r.mention for r in roles) if len(roles) != 0 else 'None', inline=False)
    )

    await ctx.respond(embed)

## Error Handler ##

@plugin.set_error_handler()
async def on_command_error(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event.exception, lightbulb.CommandNotFound):
        return
    if isinstance(event.exception, lightbulb.NotEnoughArguments):
        embed = (hikari.Embed(description='Not enough arguments were passed.\n' + ', '.join(event.exception.args), color=get_setting('embed_error_color')))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    if isinstance(event.exception, lightbulb.CommandIsOnCooldown):
        embed = (hikari.Embed(description=f'Command is on cooldown. Try again in {round(event.exception.retry_after)} second(s).', color=get_setting('embed_error_color')))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    if isinstance(event.exception, lightbulb.NotOwner):
        embed = (hikari.Embed(description=f'You do not have permission to use this command!', color=get_setting('embed_error_color')))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    embed = (hikari.Embed(description='I have errored, and I cannot get up', color=get_setting('embed_error_color')))
    await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    raise event.exception

## Definitions ##

def load(bot):
    bot.add_plugin(plugin)