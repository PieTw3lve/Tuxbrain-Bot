import hikari
import lightbulb
import miru

from datetime import datetime
from typing import Optional
from bot import get_setting

plugin = lightbulb.Plugin('General')

## Info Command ##

@plugin.listener(hikari.StartedEvent)
async def startup_info_view(event: hikari.StartedEvent):
    view = InfoView()
    await view.start()

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
            miru.SelectOption(label='💰 Economy Commands', value='economy', description='A list of economy related commands.'),
            miru.SelectOption(label='🐓 Chicken Commands', value='chicken', description='A list of chicken related commands.'),
            miru.SelectOption(label='🐧 Rushsite Commands', value='rushsite', description='A list of Rushsite related commands.'),
            miru.SelectOption(label='🎲 Fun Commands', value='fun', description='A list of fun related commands.'),
            miru.SelectOption(label='💻 Admin Commands', value='admin', description='A list of admin related commands.'),
        ]
    )
    async def select_menu(self, select: miru.Select, ctx: miru.Context) -> None:
        option = select.values[0]
        
        match option:
            case 'about':
                embed = hikari.Embed(title='💬 About', description='Tux Bot is an [open source](https://github.com/PieTw3lve/Tux_Bot), multi-use bot programmed by **Pie12#1069**. Tux Bot is written in [hikari.py](https://www.hikari-py.dev/), a new static-typed Python API for writing Discord Bot. Which means it is still in an **alpha** state, so expect some minor bugs! \n\nPlease mention or private message **Pie12#1069** if you find any bugs!', color=get_setting('embed_color'))
                embed.set_thumbnail(r'''profile\pie12.png''')
            case 'invite':
                embed = hikari.Embed(title='🤖 Invite Bot', description='Currently, there is no way to invite Tux Bot to your own personal server. However, you can download and host Tux Bot for yourself on [github](https://github.com/PieTw3lve/Tux_Bot). Instruction on how to host Tux Bot is shown down below.', color=get_setting('embed_color'))
            case 'general':
                embed = hikari.Embed(title='📝 General Commands', color=get_setting('embed_color'))
                embed.add_field('Commands', '`info`\n\n`ping`\n\n`profile`', inline=True)
                embed.add_field('Description', "Displays useful information.\n\nDisplays bot's latency.\n\nGet info on a server member.", inline=True)
                embed.add_field('Arguments', '`None`\n\n`None`\n\n`User*`', inline=True)
                embed.set_footer('symboles: [*] = optional')
            case 'economy':
                embed = hikari.Embed(title='💰 Economy Commands', color=get_setting('embed_color'))
                embed.add_field('Commands', '`balance`\n\n`daily`\n\n`pay`\n\n`coinflip`\n\n`draw`\n\n`battle`', inline=True)
                embed.add_field('Description', "Get balance on a server member.\n\nGet your daily reward!\n\nGive a server member money!\n\nFlips a coin!\n\nDraw a card from a deck.\n\nDraw a card against a bot. Winner has the highest value card.", inline=True)
                embed.add_field('Arguments', '`User*`\n\n`None`\n\n`User`, `Number`\n\n`Number`\n\n`None`\n\n`Bet`', inline=True)
                embed.set_footer('symboles: [*] = optional')
            case 'chicken':
                embed = hikari.Embed(title='🐓 Chicken Commands', color=get_setting('embed_color'))
                embed.add_field('Commands', '`cock info`\n\n\n`cock shop`\n\n`cock wilderness`\n\n\n`cock friendly`\n\n\n\n`cock sell`', inline=True)
                embed.add_field('Description', "Shows info about a sever member's cock (CHICKEN!).\n\nStart your chicken raising adventure!\n\nEnter the wilderness to fight wild cocks to gain experience and items!\n\nFight a friendly match with a server member! There will be no consequences other than losing friends.\n\nAre you bored of your feathered friend? Sell them for some coins!", inline=True)
                embed.add_field('Arguments', '`None`\n\n\n`None`\n\n`None`\n\n\n`User`\n\n\n\n`None`', inline=True)
                embed.set_footer('symboles: [*] = optional')
            case 'rushsite':
                embed = hikari.Embed(title='🐧 Rushsite Commands', color=get_setting('embed_color'))
                embed.add_field('Commands', '`rushsite signup`', inline=True)
                embed.add_field('Description', "Sign up for the current season of Rushsite!", inline=True)
                embed.add_field('Arguments', '`Logo*`', inline=True)
                embed.set_footer('symboles: [*] = optional')
            case 'fun':
                embed = hikari.Embed(title='🎲 Fun Commands', color=get_setting('embed_color'))
                embed.add_field('Commands', '`hangman`\n\n`random fox`\n\n`random cat`\n\n`random dog`\n\n`random joke`\n\n`random riddle`\n\n`random fact`\n\n`fact`\n\n`bored`', inline=True)
                embed.add_field('Description', "Play a game of Hangman!\n\nGet a random picture of a fox!\n\nGet a random picture of a cat!\n\nGet a random picture of a dog!\n\nGet a random unfunny joke!\n\nGet a random riddle!\n\nGet a random useless fact!\n\nGet the useless fact of the day!\n\nGet an activity suggestion from the bot!", inline=True)
                embed.add_field('Arguments', '`Word`, `Theme`\n\n`None`\n\n`None`\n\n`None`\n\n`None`\n\n`None`\n\n`None`\n\n`None`\n\n`None`', inline=True)
                embed.set_footer('symboles: [*] = optional')
            case 'admin':
                embed = hikari.Embed(title='💻 Admin Commands', color=get_setting('embed_color'))
                embed.add_field('Commands', '`translate`\n\n\n`admin announce`\n\n\n`admin poll`\n\n\n`admin close-poll`\n\n\n`admin rushsite-strike`\n\n\n\n`admin bet`\n\n`admin eco-set`\n\n\n`admin eco-add`\n\n\n`admin eco-take`', inline=True)
                embed.add_field('Description', "Toggles automatic text translation.\n\nMake an announcement!\n\n\nCreate a custom poll!\n\n\nClose an existing poll!\n\n\nChoose a map by taking turns elimitated maps one by one.\n\nStart a live interactive bet!\n\nSet a server member's wallet to a specific amount.\n\nAdd coins to a server member's wallet.\n\nRemove coins to a server member's wallet.", inline=True)
                embed.add_field('Arguments', '`None`\n\n\n`Channel`, `Title*`, `Message`, `Ping`, `Image*`\n\n`Title*`, `Description`, `Image`, `Options*`, `Timeout*`\n\n`Channel*`, `Message_ID*`\n\n\n`Player1`, `Player2`\n\n\n\n`option1`, `option2`\n\n`User`, `Amount`\n\n\n`User`, `Amount`, `Update`\n\n\n`User`, `Amount`, `Update`', inline=True)
                embed.set_footer('symboles: [*] = optional')
        
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
    async def view_check(self, context: miru.Context) -> bool:
        return True

@plugin.command
@lightbulb.add_cooldown(length=10.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.command('info', 'Displays useful information')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def info(ctx: lightbulb.Context) -> None:
    view = InfoView()
    
    embed = (hikari.Embed(title="Tux Bot", description='I am a simple and humble bot that can do really cool things!', color=get_setting('embed_color'))
        .set_thumbnail(r'''profile\bot.png''')
        .add_field('I have various cool features:', '• Auto Translation\n• Rushsite Integration\n• Economy Integration\n• Fun Interactive Games\n• And Many More!', inline=True)
        .add_field('Want to learn more about Tux Bot?', 'Click on 💬 **About** to learn more about Tux Bot! \n\nShoutouts to **Ryan#3388** and **BoboTheChimp#6164** for helping!', inline=True)
        .set_footer('Use the select menu below for more info!')
    )
    
    message = await ctx.respond(embed, components=view.build())
    message = await message
    
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