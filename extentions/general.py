import hikari
import lightbulb
import miru

from datetime import datetime
from typing import Optional

plugin = lightbulb.Plugin('General')

## Info Command ##

class InfoView(miru.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
    
    @miru.select(
        custom_id='info_select',
        placeholder='Choose a category',
        options=[
            miru.SelectOption(label='💬 About', value='about', description='More info about Tux Bot.'),
            miru.SelectOption(label='🤖 Invite Bot', value='invite', description='How do I invite Tux Bot to my server?'),
            miru.SelectOption(label='📝 General Commands', value='general', description='A list of general related commands.'),
            miru.SelectOption(label='💸 Economy Commands', value='economy', description='A list of economy related commands.'),
            miru.SelectOption(label='🐧 Rushsite Commands', value='rushsite', description='A list of Rushsite related commands.'),
            miru.SelectOption(label='💻 Admin Commands', value='admin', description='A list of admin related commands.'),
            miru.SelectOption(label='🌎 Translation', value='translation', description='Why is the the Bot replying to me?')
        ]
    )
    async def select_menu(self, select: miru.Select, ctx: miru.Context) -> None:
        option = select.values[0]
        
        match option:
            case 'about':
                embed = hikari.Embed(title='💬 About', description='Tux Bot is an [open source](https://github.com/PieTw3lve/Tux_Bot), multi-use bot programmed by **Pie12#1069**. Tux Bot is written in [hikari.py](https://www.hikari-py.dev/), a new static-typed Python API for writing Discord Bot. Which means it is still in an **alpha** state, so expect some minor bugs! \n\nPlease mention or private message **Pie12#1069** if you find any bugs!', color='#249EDB')
                embed.set_thumbnail('Pie12.png')
            case 'invite':
                embed = hikari.Embed(title='🤖 Invite Bot', description='Currently, there is no way to invite Tux Bot to your own personal server. \nHowever, this may change in the future.', color='#249EDB')
            case 'general':
                embed = hikari.Embed(title='📝 General Commands', color='#249EDB')
                embed.add_field('Commands', '`info` \n\n `ping` \n\n `profile`', inline=True)
                embed.add_field('Description', "Displays useful information. \n\n Displays bot's latency. \n\n Get info on a server member.", inline=True)
                embed.add_field('Arguments', '`None` \n\n `None` \n\n `User*`', inline=True)
                embed.set_footer('symboles: [*] = optional')
            case 'economy':
                embed = hikari.Embed(title='💸 Economy Commands', color='#249EDB')
                embed.add_field('Commands', '`balance` \n\n `daily` \n\n `pay` \n\n `coinflip` \n\n `draw` \n\n `battle` ', inline=True)
                embed.add_field('Description', "Get balance on a server member. \n\n Get your daily reward! \n\n Give a server member money! \n\n Flips a coin! \n\n Draw a card from a deck. \n\n Draw a card against a bot. Winner has the highest value card.", inline=True)
                embed.add_field('Arguments', '`User*` \n\n `None` \n\n `User`, `Number` \n\n `Number` \n\n `None` \n\n `Bet`', inline=True)
                embed.set_footer('symboles: [*] = optional')
            case 'rushsite':
                embed = hikari.Embed(title='🐧 Rushsite Commands', color='#249EDB')
                embed.add_field('Commands', '`None`', inline=True)
                embed.add_field('Description', "None", inline=True)
                embed.add_field('Arguments', '`None`', inline=True)
                embed.set_footer('symboles: [*] = optional')
            case 'admin':
                embed = hikari.Embed(title='💻 Admin Commands', color='#249EDB')
                embed.add_field('Commands', '`admin announce` \n\n `admin strike`', inline=True)
                embed.add_field('Description', "Make an announcement! \n\n Choose a map by taking turns elimitated maps one by one.", inline=True)
                embed.add_field('Arguments', '`Channel`, `Title*`, `Message`, `Ping`, `Image*` \n\n `Player1`, `Player2`', inline=True)
                embed.set_footer('symboles: [*] = optional')
            case 'translation':
                embed = hikari.Embed(title='🌎 Translation', description="Tux Bot's translation feature integrates Google Translate API to translate users' messages automatically. In addition, Tux Bot includes a confidence value next to the detected language because we all know Google Translate sucks occasionally. The maximum confidence value is `1.0` and the minimum value is `0.0`.", color='#249EDB')
        
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
    async def view_check(self, context: miru.Context) -> bool:
        return True

@plugin.command
@lightbulb.add_cooldown(length=10.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.command('info', 'Displays useful information')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def info(ctx: lightbulb.Context) -> None:
    view = InfoView()
    
    embed = (hikari.Embed(title="Tux Bot", description='I am a simple and humble bot that can do really cool things!', color='#249EDB')
        .set_thumbnail('bot.png')
        .add_field('I have various cool features:', '• Auto Translation\n• Rushsite Integration\n• Economy Integration\n• Fun Interactive Games\n• And Many More!', inline=True)
        .add_field('Want to learn more about Tux Bot?', 'Click on 💬 **About** to learn more about Tux Bot! \n\n Shoutouts to **Ryan#3388** and **BoboTheChimp#6164** for helping!', inline=True)
        .set_footer('Use the select menu below for more info!')
    )
    
    message = await ctx.respond(embed, components=view.build())
    message = await message
    
    view.start(message)

## Ping Command ##

@plugin.command
@lightbulb.add_cooldown(length=10.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.command('ping', "Displays bot's latency.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def ping(ctx: lightbulb.Context) -> None:
    embed = (hikari.Embed(title='Pong!', description=f'{round(ctx.bot.heartbeat_latency * 1000)}ms 📶', color='#249EDB'))
    await ctx.respond(embed)

## Profile Command ##

@plugin.command
@lightbulb.add_cooldown(length=10.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.option('user', 'The user to get information about.', hikari.User, required=False)
@lightbulb.command('profile', 'Get info on a server member.', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def profile(ctx: lightbulb.Context, user: Optional[hikari.User] = None) -> None:
    if not (guild := ctx.get_guild()):
        await ctx.respond('This command may only be used in servers.')
        return

    user = user or ctx.author
    user = ctx.bot.cache.get_member(guild, user)
    
    if not user:
        await ctx.respond('That user is not in the server.')
        return
    
    created_at = int(user.created_at.timestamp())
    joined_at = int(user.joined_at.timestamp())
    
    roles = (await user.fetch_roles())[1:]  # All but @everyone
    roles = sorted(roles, key=lambda role: role.position, reverse=True)  # sort them by position, then reverse the order to go from top role down

    embed = (
        hikari.Embed(title=f'User Info - {user.display_name}', description=f'ID: `{user.id}`', color='#249EDB', timestamp=datetime.now().astimezone())
        .set_footer(text=f'Requested by {ctx.author.username}', icon=ctx.author.display_avatar_url)
        .set_thumbnail(user.avatar_url)
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
        embed = (hikari.Embed(description='Not enough arguments were passed.\n' + ', '.join(event.exception.args), color='#FF0000'))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    if isinstance(event.exception, lightbulb.CommandIsOnCooldown):
        embed = (hikari.Embed(description=f'Command is on cooldown. Try again in {round(event.exception.retry_after)} second(s).', color='#FF0000'))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    if isinstance(event.exception, lightbulb.NotOwner):
        embed = (hikari.Embed(description=f'You do not have permission to use this command!', color='#FF0000'))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    embed = (hikari.Embed(description='I have errored, and I cannot get up', color='#FF0000'))
    await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    raise event.exception

## Add as a plugin ##

def load(bot):
    bot.add_plugin(plugin)