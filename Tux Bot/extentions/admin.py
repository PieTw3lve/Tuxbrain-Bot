import hikari
import lightbulb
import miru

plugin = lightbulb.Plugin('Admin')

## Admin Subcommand ##

@plugin.command
@lightbulb.command('admin', 'Every command related to administration.')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommandGroup)
async def admin(ctx: lightbulb.Context) -> None:
    return

## Announcement Command ##

@admin.child
@lightbulb.option('image', 'Announcement attachment.', type=hikari.Attachment, required=False)
@lightbulb.option('ping', 'Role to ping with announcement.', type=hikari.Role, required=True)
@lightbulb.option('message', 'The message to announce.', type=str, required=True)
@lightbulb.option('title', 'The message to announce.', type=str, required=False)
@lightbulb.option('channel', 'Channel to post announcement to.', type=hikari.TextableChannel, required=True)
@lightbulb.command('announce', 'Make an announcement!', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def announce(ctx: lightbulb.Context, title: str, message: str, image: hikari.Attachment, channel: hikari.InteractionChannel, ping: hikari.Role) -> None:
    embed = hikari.Embed(title=title, description=message, color='#249EDB')
    embed.set_image(image)

    await ctx.bot.rest.create_message(content=ping.mention, channel=channel.id, embed=embed, role_mentions=True)

    await ctx.respond(f"Announcement posted to <#{channel.id}>!", flags=hikari.MessageFlag.EPHEMERAL)

## Rushsite Strike Command ##

class Option1(miru.SelectOption):
    def __init__(self) -> None:
        super().__init__(label='Vertigo', value='Vertigo')

class Option2(miru.SelectOption):
    def __init__(self) -> None:
        super().__init__(label='Cobblestone', value='Cobblestone')

class Option3(miru.SelectOption):
    def __init__(self) -> None:
        super().__init__(label='Train', value='Train')

class Option4(miru.SelectOption):
    def __init__(self) -> None:
        super().__init__(label='Shortdust', value='Shortdust')

class Option5(miru.SelectOption):
    def __init__(self) -> None:
        super().__init__(label='Blagai', value='Blagai')
        
class Option6(miru.SelectOption):
    def __init__(self) -> None:
        super().__init__(label='Overpass', value='Overpass')
        
class Option7(miru.SelectOption):
    def __init__(self) -> None:
        super().__init__(label='Nuke ', value='Nuke')

class CTButton(miru.Button):
    def __init__(self) -> None:
        super().__init__(style=hikari.ButtonStyle.PRIMARY, label='Counter-Terrorist')
    
    async def callback(self, ctx: miru.Context) -> None:
        self.view.side = 'CT'
        self.view.stop()

class TButton(miru.Button):
    def __init__(self) -> None:
        super().__init__(style=hikari.ButtonStyle.DANGER, label='Terrorist')
    
    async def callback(self, ctx: miru.Context) -> None:
        self.view.side = 'T'
        self.view.stop()

class StrikeOptions(miru.Select):
    def __init__(self, options: list) -> None:
        self.maps = []
        
        for map in options:
            match map:
                case 'Vertigo':
                    self.maps.append(Option1())
                case 'Cobblestone':
                    self.maps.append(Option2())
                case 'Train':
                    self.maps.append(Option3())
                case 'Shortdust':
                    self.maps.append(Option4())
                case 'Blagai':
                    self.maps.append(Option5())
                case 'Overpass':
                    self.maps.append(Option6())
                case 'Nuke':
                    self.maps.append(Option7()) 
        
        super().__init__(options=self.maps, custom_id='map_select', placeholder='Select a map')
    
    async def callback(self, ctx: miru.Context) -> None:
        self.view.map = ctx.interaction.values[0]
        self.view.stop()

class Strike(miru.View):
    def __init__(self, player1: hikari.User, player2: hikari.User, round: int) -> None:
        self.player1 = player1
        self.player2 = player2
        self.round = round
        
        super().__init__(timeout=None)
                        
    async def on_timeout(self) -> None:
        embed = hikari.Embed(description='The menu has timed out.', color='#249EDB')
        await self.message.edit(embed, components=[])
    
    async def view_check(self, ctx: miru.Context) -> bool:
        if self.round % 2 == 0: # checks if round number is even
            return ctx.user.id == self.player2.id
        else:
            return ctx.user.id == self.player1.id

class CheckView(miru.View):
    def __init__(self, player1: hikari.User) -> None:
        self.player = player1
        super().__init__(timeout=None)
        
    async def on_timeout(self) -> None:
        embed = hikari.Embed(description='The menu has timed out.', color='#249EDB')
        await self.message.edit(embed, components=[])
        
    async def view_check(self, ctx: miru.Context) -> bool:
        return ctx.user.id == self.player.id

@admin.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option('player2', 'The user that will strike second.', type=hikari.User, required=True)
@lightbulb.option('player1', 'The user that will strike first.', type=hikari.User, required=True)
@lightbulb.command('strike', 'Choose a map by taking turns elimitated maps one by one.', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def strike(ctx: lightbulb.Context, player1: hikari.User, player2: hikari.User) -> None:
    maps = ['Vertigo', 'Cobblestone', 'Train', 'Shortdust', 'Blagai', 'Overpass', 'Nuke']
    round = 1
    
    image = r'''maps\anthony_meyer_joker.jpg'''
    
    view = Strike(player1, player2, round)
    view.add_item(StrikeOptions(maps))
    embed = hikari.Embed(title=f'{player1} Choose a stage to eliminate!', color='#249EDB')
    embed.set_image(image)
    message = await ctx.respond(embed, components=view.build())
    message = await message
    view.start(message)
    
    await view.wait()
    
    while True:
        if hasattr(view, 'map'): # identifies which map has been chosen and removes it from selection
            map = view.map
            match map:
                case 'Vertigo':
                    maps.remove(map)
                    round = round + 1
                case 'Cobblestone':
                    maps.remove(map)
                    round = round + 1
                case 'Train':
                    maps.remove(map)
                    round = round + 1
                case 'Shortdust':
                    maps.remove(map)
                    round = round + 1
                case 'Blagai':
                    maps.remove(map)
                    round = round + 1
                case 'Overpass':
                    maps.remove(map)
                    round = round + 1
                case 'Nuke': 
                    maps.remove(map)
                    round = round + 1
        # displays which map got eliminated and current player turn
        if round % 2 == 0:
            embed = hikari.Embed(title=f'{player2} Choose a stage to eliminate!', description=f'{player1} eliminated **{map}**!', color='#249EDB')
            embed.set_image(image)
        else:
            embed = hikari.Embed(title=f'{player1} Choose a stage to eliminate!', description=f'{player2} eliminated **{map}**!', color='#249EDB')
            embed.set_image(image)
        # ends strike if map remains
        if len(maps) <= 1:
            break
        # updates message and map choices if there's more than one map
        view = Strike(player1, player2, round)
        view.add_item(StrikeOptions(maps))
        message = await ctx.edit_last_response(embed, components=view.build())
        view.start(message)
        await view.wait()
        
    # player1 choose which side to start on
    
    winner = maps[0]
    image = set_stage_image(winner)
    side1 = ''
    side2 = ''
    
    view = CheckView(player1)
    view.add_item(CTButton())
    view.add_item(TButton())
    
    embed = hikari.Embed(title=f'**{player1}** Choose your starting side on {winner}:', color='#249EDB')
    embed.set_image(image)
    message = await ctx.edit_last_response(embed, components=view.build())
    view.start(message)
    
    await view.wait()
    
    if hasattr(view, 'side'):
        match view.side:
            case 'CT':
                side1 = 'Counter-Terrorist'
                side2 = 'Terrorist'
            case 'T':
                side1 = 'Terrorist'
                side2 = 'Counter-Terrorist'
                            
    # display strike results
    
    embed = hikari.Embed(title=f'Strike Results:', description=f'The chosen map is **{winner}**!\n\n{player1} will start on **{side1}**!\n{player2} will start on **{side2}**!', color='#249EDB')
    embed.set_image(image)
    await ctx.edit_last_response(embed, components=[])

def set_stage_image(map):
    match map:
        case 'Vertigo':
            return r'''maps\vertigo.png'''
        case 'Cobblestone':
            return r'''maps\cobblestone.png'''
        case 'Train':
            return r'''maps\train.png'''
        case 'Shortdust':
            return r'''maps\shortdust.png'''
        case 'Blagai':
            return r'''maps\blagai.png'''
        case 'Overpass':
            return r'''maps\overpass.png'''
        case 'Nuke': 
            return r'''maps\nuke.png'''

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