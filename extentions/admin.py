import hikari
import lightbulb
import miru
import sqlite3

from datetime import datetime
from bot import get_setting, write_setting, verify_user
from .economy import add_money, set_money, remove_money
from .rushite import set_stage_image

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
        embed = hikari.Embed(title=self.header.value, description=self.message.value, color=get_setting('embed_important_color'))
        embed.set_image(self.image)
        
        await ctx.bot.rest.create_message(content=self.ping.mention, channel=self.channel.id, embed=embed, role_mentions=True)
        
        embed = hikari.Embed(title='Success!', description=f'Announcement posted to <#{self.channel.id}>!', color=get_setting('embed_color'))
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
        color=get_setting('embed_color'),
        timestamp=datetime.now().astimezone()
    )
    embed.set_image(image)
    embed.set_thumbnail(r'''game_preview\poll.png''')
    
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
        
        embed = hikari.Embed(description='You already voted!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def printProgressBar (iteration, total, prefix: str, suffix: str, decimals = 1, length = 100, fill = '▰', empty = '▱'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + empty * (length - filledLength)
    
    return f'\r{prefix} {bar} {percent}% {suffix}'

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
        embed.color = get_setting('embed_success_color')
    except:
        embed.description = 'Could not located message!'
        embed.color = get_setting('embed_error_color')
    
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

## Rushsite Open Signup Command ## 

@admin.child
@lightbulb.option('status', 'If server members can use the command.', type=bool, required=True)
@lightbulb.command('rushsite-signup-status', 'Set accessibility to signup command.', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def set_signup_status(ctx: lightbulb.Context, status: hikari.TextableChannel) -> None:
    try:
        write_setting('rushsite_signup_accessible', status)
        embed = hikari.Embed(description=f'Successfully set accessibility to {status}!', color=get_setting('embed_success_color'))
    except:
        embed = hikari.Embed(description=f'Failed to set accessibility!', color=get_setting('embed_error_color'))
        
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

## Rushsite Set Signup Channel Command ## 

@admin.child
@lightbulb.option('channel', 'The channel Tux Bot will post signup forms.', type=hikari.TextableChannel, required=True)
@lightbulb.command('rushsite-signup-channel', 'Set the default signup channel.', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def set_signup_channel(ctx: lightbulb.Context, channel: hikari.TextableChannel) -> None:
    try:
        write_setting('rushsite_signup_channel', channel.id)
        embed = hikari.Embed(description=f'Successfully set default channel to <#{channel.id}>!', color=get_setting('embed_success_color'))
    except:
        embed = hikari.Embed(description=f'Failed to set default channel!', color=get_setting('embed_error_color'))
        
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

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
        embed = hikari.Embed(description='The menu has timed out.', color=get_setting('embed_color'))
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
        embed = hikari.Embed(description='The menu has timed out.', color=get_setting('embed_color'))
        await self.message.edit(embed, components=[])
        
    async def view_check(self, ctx: miru.Context) -> bool:
        return ctx.user.id == self.player.id

@admin.child
@lightbulb.option('player2', 'The user that will strike second.', type=hikari.User, required=True)
@lightbulb.option('player1', 'The user that will strike first.', type=hikari.User, required=True)
@lightbulb.command('rushsite-strike', 'Choose a map by taking turns elimitated maps one by one.', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def strike(ctx: lightbulb.Context, player1: hikari.User, player2: hikari.User) -> None:
    maps = ['Vertigo', 'Cobblestone', 'Train', 'Shortdust', 'Blagai', 'Overpass', 'Nuke']
    round = 1
    
    image = r'''maps\anthony_meyer_joker.jpg'''
    
    view = Strike(player1, player2, round)
    view.add_item(StrikeOptions(maps))
    embed = hikari.Embed(title=f'{player1} Choose a stage to eliminate!', color=get_setting('embed_color'))
    embed.set_image(image)
    message = await ctx.respond(embed, components=view.build())
    message = await message
    await view.start(message)
    
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
            embed = hikari.Embed(title=f'{player2} Choose a stage to eliminate!', description=f'{player1} eliminated **{map}**!', color=get_setting('embed_color'))
            embed.set_image(image)
        else:
            embed = hikari.Embed(title=f'{player1} Choose a stage to eliminate!', description=f'{player2} eliminated **{map}**!', color=get_setting('embed_color'))
            embed.set_image(image)
        # ends strike if map remains
        if len(maps) <= 1:
            break
        # updates message and map choices if there's more than one map
        view = Strike(player1, player2, round)
        view.add_item(StrikeOptions(maps))
        message = await ctx.edit_last_response(embed, components=view.build())
        await view.start(message)
        await view.wait()
        
    # player1 choose which side to start on
    
    winner = maps[0]
    image = set_stage_image(winner)
    side1 = ''
    side2 = ''
    
    view = CheckView(player1)
    view.add_item(CTButton())
    view.add_item(TButton())
    
    embed = hikari.Embed(title=f'**{player1}** Choose your starting side on {winner}:', color=get_setting('embed_color'))
    embed.set_image(image)
    message = await ctx.edit_last_response(embed, components=view.build())
    await view.start(message)
    
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
    
    embed = hikari.Embed(title=f'Strike Results:', description=f'The chosen map is **{winner}**!\n\n{player1} will start on **{side1}**!\n{player2} will start on **{side2}**!', color=get_setting('embed_color'))
    embed.set_image(image)
    await ctx.edit_last_response(embed, components=[])

## Bet Command ##

class BetView(miru.View):
    def __init__(self, author: hikari.User, option1: str, option2: str) -> None:
        super().__init__(timeout=None)
        self.author = author
        self.bet1 = {}
        self.bet2 = {}
        self.option1 = option1
        self.option2 = option2
        
        self.percentage1 = 50
        self.total1 = 0
        self.payout1 = 0
        self.participant1 = []
        self.highest1 = 0
        self.highest1User = 'N/A'
        
        self.percentage2 = 50
        self.total2 = 0
        self.payout2 = 0
        self.participant2 = []
        self.highest2 = 0
        self.highest2User = 'N/A'
        
        self.db = sqlite3.connect('database.sqlite')
        self.cursor = self.db.cursor()
    
    # Option 1 Bet Buttons
    
    @miru.button(label='50', emoji='🪙', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def bet_50_option1(self, button: miru.Button, ctx: miru.Context) -> None:
        user = ctx.user
        amount = 50
        
        if verify_user(user) == None: # if user has never been register
            embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        self.cursor.execute(f'SELECT balance FROM database WHERE user_id = {user.id}') # moves cursor to user's balance from database
        bal = self.cursor.fetchone() # grabs the value of user's balance
        
        try: # just in case for errors
            balance = bal[0] # balance SHOULD be at index 0
        except:
            balance = 0
            
        if balance < amount: # checks if sender has enough money to send the specified amount
            embed = hikari.Embed(description='You do not have enough money to bet!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif user_had_bets(self.bet2, user): 
            embed = hikari.Embed(description="You can only bet on one side!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        else:
            if user_had_bets(self.bet1, user):
                self.bet1[user.id] = add_bet(self.bet1, user, amount)
            else:
                self.bet1.update({user.id: amount})
                self.participant1.append(user.id)
        
        sql = ('UPDATE database SET balance = ? WHERE user_id = ?') # update user's new balance in database
        val = (balance - (amount), user.id)
        embed = (hikari.Embed(title='Success!', description=f'Your total coins on **Green** is 🪙 {(self.bet1[user.id]):,}!\nNew Balance: 🪙 {(balance - amount):,}', color=get_setting('embed_success_color')))

        self.cursor.execute(sql, val) # executes the instructions
        self.db.commit() # saves changes
    
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        self.total1 = self.total1 + amount
        
        self.percentage1 = 100 * (self.total1/(self.total1 + self.total2))
        self.percentage2 = 100 * (self.total2/(self.total1 + self.total2))
        
        bet = get_bet(self.bet1)
        self.payout1 = (bet + (bet/self.total1) * self.total2)/bet
        
        if self.total2 != 0:
            bet = get_bet(self.bet1)
            self.payout2 = (bet + (bet/self.total2) * self.total1)/bet
        
        if self.bet1[user.id] > self.highest1:
            self.highest1 = self.bet1[user.id]
            self.highest1User = user

        embed = (hikari.Embed(title="Bets are open!", color=get_setting('embed_color'))
        .add_field(f'{self.option1} (Green) {self.percentage1:.0f}%', f'Total Coins: 🪙 {self.total1:,}\nPayout: 💸 {self.payout1:.2f}\nParticipants: 👥 {len(self.participant1):,}\nHighest Bet: 🪙 {self.highest1:,} ({self.highest1User})', inline=True)
        .add_field(f'{self.option2} (Blue) {self.percentage2:.0f}%', f'Total Coins: 🪙 {self.total2:,}\nPayout: 💸 {self.payout2:.2f}\nParticipants: 👥 {len(self.participant2):,}\nHighest Bet: 🪙 {self.highest2:,} ({self.highest2User})', inline=True)
        )
        
        await self.message.edit(embed)
    
    @miru.button(label='100', emoji='🪙', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def bet_100_option1(self, button: miru.Button, ctx: miru.Context) -> None:
        user = ctx.user
        amount = 100
        
        if verify_user(user) == None: # if user has never been register
            embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        self.cursor.execute(f'SELECT balance FROM database WHERE user_id = {user.id}') # moves cursor to user's balance from database
        bal = self.cursor.fetchone() # grabs the value of user's balance
        
        try: # just in case for errors
            balance = bal[0] # balance SHOULD be at index 0
        except:
            balance = 0
            
        if balance < amount: # checks if sender has enough money to send the specified amount
            embed = hikari.Embed(description='You do not have enough money to bet!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif user_had_bets(self.bet2, user): 
            embed = hikari.Embed(description="You can only bet on one side!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        else:
            if user_had_bets(self.bet1, user):
                self.bet1[user.id] = add_bet(self.bet1, user, amount)
            else:
                self.bet1.update({user.id: amount})
                self.participant1.append(user.id)
        
        sql = ('UPDATE database SET balance = ? WHERE user_id = ?') # update user's new balance in database
        val = (balance - (amount), user.id)
        embed = (hikari.Embed(title='Success!', description=f'Your total coins on **Green** is 🪙 {(self.bet1[user.id]):,}!\nNew Balance: 🪙 {(balance - amount):,}', color=get_setting('embed_success_color')))

        self.cursor.execute(sql, val) # executes the instructions
        self.db.commit() # saves changes
    
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        self.total1 = self.total1 + amount
        
        self.percentage1 = 100 * (self.total1/(self.total1 + self.total2))
        self.percentage2 = 100 * (self.total2/(self.total1 + self.total2))
        
        bet = get_bet(self.bet1)
        self.payout1 = (bet + (bet/self.total1) * self.total2)/bet
        
        if self.total2 != 0:
            bet = get_bet(self.bet1)
            self.payout2 = (bet + (bet/self.total2) * self.total1)/bet
        
        if self.bet1[user.id] > self.highest1:
            self.highest1 = self.bet1[user.id]
            self.highest1User = user

        embed = (hikari.Embed(title="Bets are open!", color=get_setting('embed_color'))
        .add_field(f'{self.option1} (Green) {self.percentage1:.0f}%', f'Total Coins: 🪙 {self.total1:,}\nPayout: 💸 {self.payout1:.2f}\nParticipants: 👥 {len(self.participant1):,}\nHighest Bet: 🪙 {self.highest1:,} ({self.highest1User})', inline=True)
        .add_field(f'{self.option2} (Blue) {self.percentage2:.0f}%', f'Total Coins: 🪙 {self.total2:,}\nPayout: 💸 {self.payout2:.2f}\nParticipants: 👥 {len(self.participant2):,}\nHighest Bet: 🪙 {self.highest2:,} ({self.highest2User})', inline=True)
        )
        
        await self.message.edit(embed)
    
    @miru.button(label='500', emoji='🪙', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def bet_500_option1(self, button: miru.Button, ctx: miru.Context) -> None:
        user = ctx.user
        amount = 500
        
        if verify_user(user) == None: # if user has never been register
            embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        self.cursor.execute(f'SELECT balance FROM database WHERE user_id = {user.id}') # moves cursor to user's balance from database
        bal = self.cursor.fetchone() # grabs the value of user's balance
        
        try: # just in case for errors
            balance = bal[0] # balance SHOULD be at index 0
        except:
            balance = 0
            
        if balance < amount: # checks if sender has enough money to send the specified amount
            embed = hikari.Embed(description='You do not have enough money to bet!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif user_had_bets(self.bet2, user): 
            embed = hikari.Embed(description="You can only bet on one side!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        else:
            if user_had_bets(self.bet1, user):
                self.bet1[user.id] = add_bet(self.bet1, user, amount)
            else:
                self.bet1.update({user.id: amount})
                self.participant1.append(user.id)
        
        sql = ('UPDATE database SET balance = ? WHERE user_id = ?') # update user's new balance in database
        val = (balance - (amount), user.id)
        embed = (hikari.Embed(title='Success!', description=f'Your total coins on **Green** is 🪙 {(self.bet1[user.id]):,}!\nNew Balance: 🪙 {(balance - amount):,}', color=get_setting('embed_success_color')))

        self.cursor.execute(sql, val) # executes the instructions
        self.db.commit() # saves changes
    
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        self.total1 = self.total1 + amount
        
        self.percentage1 = 100 * (self.total1/(self.total1 + self.total2))
        self.percentage2 = 100 * (self.total2/(self.total1 + self.total2))
        
        bet = get_bet(self.bet1)
        self.payout1 = (bet + (bet/self.total1) * self.total2)/bet
        
        if self.total2 != 0:
            bet = get_bet(self.bet1)
            self.payout2 = (bet + (bet/self.total2) * self.total1)/bet
        
        if self.bet1[user.id] > self.highest1:
            self.highest1 = self.bet1[user.id]
            self.highest1User = user

        embed = (hikari.Embed(title="Bets are open!", color=get_setting('embed_color'))
        .add_field(f'{self.option1} (Green) {self.percentage1:.0f}%', f'Total Coins: 🪙 {self.total1:,}\nPayout: 💸 {self.payout1:.2f}\nParticipants: 👥 {len(self.participant1):,}\nHighest Bet: 🪙 {self.highest1:,} ({self.highest1User})', inline=True)
        .add_field(f'{self.option2} (Blue) {self.percentage2:.0f}%', f'Total Coins: 🪙 {self.total2:,}\nPayout: 💸 {self.payout2:.2f}\nParticipants: 👥 {len(self.participant2):,}\nHighest Bet: 🪙 {self.highest2:,} ({self.highest2User})', inline=True)
        )
        
        await self.message.edit(embed)
    
    # Option 2 Bet Buttons
    
    @miru.button(label='50', emoji='🪙', style=hikari.ButtonStyle.PRIMARY, row=2)
    async def bet_50_option2(self, button: miru.Button, ctx: miru.Context) -> None:
        user = ctx.user
        amount = 50
        
        if verify_user(user) == None: # if user has never been register
            embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        self.cursor.execute(f'SELECT balance FROM database WHERE user_id = {user.id}') # moves cursor to user's balance from database
        bal = self.cursor.fetchone() # grabs the value of user's balance
        
        try: # just in case for errors
            balance = bal[0] # balance SHOULD be at index 0
        except:
            balance = 0
            
        if balance < amount: # checks if sender has enough money to send the specified amount
            embed = hikari.Embed(description='You do not have enough money to bet!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif user_had_bets(self.bet1, user): 
            embed = hikari.Embed(description="You can only bet on one side!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        else:
            if user_had_bets(self.bet2, user):
                self.bet2[user.id] = add_bet(self.bet2, user, amount)
            else:
                self.bet2.update({user.id: amount})
                self.participant2.append(user.id)
        
        sql = ('UPDATE database SET balance = ? WHERE user_id = ?') # update user's new balance in database
        val = (balance - (amount), user.id)
        embed = (hikari.Embed(title='Success!', description=f'Your total coins on **Blue** is 🪙 {(self.bet2[user.id]):,}!\nNew Balance: 🪙 {(balance - amount):,}', color=get_setting('embed_success_color')))

        self.cursor.execute(sql, val) # executes the instructions
        self.db.commit() # saves changes
    
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        self.total2 = self.total2 + amount
        
        self.percentage1 = 100 * (self.total1/(self.total1 + self.total2))
        self.percentage2 = 100 * (self.total2/(self.total1 + self.total2))
        
        bet = get_bet(self.bet2)
        self.payout2 = (bet + (bet/self.total2) * self.total1)/bet
        if self.total1 != 0:
            bet = get_bet(self.bet1)
            self.payout1 = (bet + (bet/self.total1) * self.total2)/bet
        if self.bet2[user.id] > self.highest2:
            self.highest2 = self.bet2[user.id]
            self.highest2User = user

        embed = (hikari.Embed(title="Bets are open!", color=get_setting('embed_color'))
        .add_field(f'{self.option1} (Green) {self.percentage1:.0f}%', f'Total Coins: 🪙 {self.total1:,}\nPayout: 💸 {self.payout1:.2f}\nParticipants: 👥 {len(self.participant1):,}\nHighest Bet: 🪙 {self.highest1:,} ({self.highest1User})', inline=True)
        .add_field(f'{self.option2} (Blue) {self.percentage2:.0f}%', f'Total Coins: 🪙 {self.total2:,}\nPayout: 💸 {self.payout2:.2f}\nParticipants: 👥 {len(self.participant2):,}\nHighest Bet: 🪙 {self.highest2:,} ({self.highest2User})', inline=True)
        )
        
        await self.message.edit(embed)
    
    @miru.button(label='100', emoji='🪙', style=hikari.ButtonStyle.PRIMARY, row=2)
    async def bet_100_option2(self, button: miru.Button, ctx: miru.Context) -> None:
        user = ctx.user
        amount = 100
        
        if verify_user(user) == None: # if user has never been register
            embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        self.cursor.execute(f'SELECT balance FROM database WHERE user_id = {user.id}') # moves cursor to user's balance from database
        bal = self.cursor.fetchone() # grabs the value of user's balance
        
        try: # just in case for errors
            balance = bal[0] # balance SHOULD be at index 0
        except:
            balance = 0
            
        if balance < amount: # checks if sender has enough money to send the specified amount
            embed = hikari.Embed(description='You do not have enough money to bet!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif user_had_bets(self.bet1, user): 
            embed = hikari.Embed(description="You can only bet on one side!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        else:
            if user_had_bets(self.bet2, user):
                self.bet2[user.id] = add_bet(self.bet2, user, amount)
            else:
                self.bet2.update({user.id: amount})
                self.participant2.append(user.id)
        
        sql = ('UPDATE database SET balance = ? WHERE user_id = ?') # update user's new balance in database
        val = (balance - (amount), user.id)
        embed = (hikari.Embed(title='Success!', description=f'Your total coins on **Blue** is 🪙 {(self.bet2[user.id]):,}!\nNew Balance: 🪙 {(balance - amount):,}', color=get_setting('embed_success_color')))

        self.cursor.execute(sql, val) # executes the instructions
        self.db.commit() # saves changes
    
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        self.total2 = self.total2 + amount
        
        self.percentage1 = 100 * (self.total1/(self.total1 + self.total2))
        self.percentage2 = 100 * (self.total2/(self.total1 + self.total2))
        
        bet = get_bet(self.bet2)
        self.payout2 = (bet + (bet/self.total2) * self.total1)/bet
        if self.total1 != 0:
            bet = get_bet(self.bet1)
            self.payout1 = (bet + (bet/self.total1) * self.total2)/bet
        
        if self.bet2[user.id] > self.highest2:
            self.highest2 = self.bet2[user.id]
            self.highest2User = user

        embed = (hikari.Embed(title="Bets are open!", color=get_setting('embed_color'))
        .add_field(f'{self.option1} (Green) {self.percentage1:.0f}%', f'Total Coins: 🪙 {self.total1:,}\nPayout: 💸 {self.payout1:.2f}\nParticipants: 👥 {len(self.participant1):,}\nHighest Bet: 🪙 {self.highest1:,} ({self.highest1User})', inline=True)
        .add_field(f'{self.option2} (Blue) {self.percentage2:.0f}%', f'Total Coins: 🪙 {self.total2:,}\nPayout: 💸 {self.payout2:.2f}\nParticipants: 👥 {len(self.participant2):,}\nHighest Bet: 🪙 {self.highest2:,} ({self.highest2User})', inline=True)
        )
        
        await self.message.edit(embed)
    
    @miru.button(label='500', emoji='🪙', style=hikari.ButtonStyle.PRIMARY, row=2)
    async def bet_500_option2(self, button: miru.Button, ctx: miru.Context) -> None:
        user = ctx.user
        amount = 500
        
        if verify_user(user) == None: # if user has never been register
            embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        self.cursor.execute(f'SELECT balance FROM database WHERE user_id = {user.id}') # moves cursor to user's balance from database
        bal = self.cursor.fetchone() # grabs the value of user's balance
        
        try: # just in case for errors
            balance = bal[0] # balance SHOULD be at index 0
        except:
            balance = 0
            
        if balance < amount: # checks if sender has enough money to send the specified amount
            embed = hikari.Embed(description='You do not have enough money to bet!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif user_had_bets(self.bet1, user): 
            embed = hikari.Embed(description="You can only bet on one side!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        else:
            if user_had_bets(self.bet2, user):
                self.bet2[user.id] = add_bet(self.bet2, user, amount)
            else:
                self.bet2.update({user.id: amount})
                self.participant2.append(user.id)
        
        sql = ('UPDATE database SET balance = ? WHERE user_id = ?') # update user's new balance in database
        val = (balance - (amount), user.id)
        embed = (hikari.Embed(title='Success!', description=f'Your total coins on **Blue** is 🪙 {(self.bet2[user.id]):,}!\nNew Balance: 🪙 {(balance - amount):,}', color=get_setting('embed_success_color')))

        self.cursor.execute(sql, val) # executes the instructions
        self.db.commit() # saves changes
    
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        self.total2 = self.total2 + amount
        
        self.percentage1 = 100 * (self.total1/(self.total1 + self.total2))
        self.percentage2 = 100 * (self.total2/(self.total1 + self.total2))
        
        bet = get_bet(self.bet2)
        self.payout2 = (bet + (bet/self.total2) * self.total1)/bet
        if self.total1 != 0:
            bet = get_bet(self.bet1)
            self.payout1 = (bet + (bet/self.total1) * self.total2)/bet
        
        if self.bet2[user.id] > self.highest2:
            self.highest2 = self.bet2[user.id]
            self.highest2User = user

        embed = (hikari.Embed(title="Bets are open!", color=get_setting('embed_color'))
        .add_field(f'{self.option1} (Green) {self.percentage1:.0f}%', f'Total Coins: 🪙 {self.total1:,}\nPayout: 💸 {self.payout1:.2f}\nParticipants: 👥 {len(self.participant1):,}\nHighest Bet: 🪙 {self.highest1:,} ({self.highest1User})', inline=True)
        .add_field(f'{self.option2} (Blue) {self.percentage2:.0f}%', f'Total Coins: 🪙 {self.total2:,}\nPayout: 💸 {self.payout2:.2f}\nParticipants: 👥 {len(self.participant2):,}\nHighest Bet: 🪙 {self.highest2:,} ({self.highest2User})', inline=True)
        )
        
        await self.message.edit(embed)
    
    # other functions
    
    async def on_timeout(self) -> None:
        embed = (hikari.Embed(title="Bets are closed!", color=get_setting('embed_color'))
        .add_field(f'{self.option1} (Green) {self.percentage1:.0f}%', f'Total Bets: 🪙 {self.total1:,}\nPayout: 💸 {self.payout1:.2f}\nParticipants: 👥 {len(self.participant1):,}\nHighest Bet: 🪙 {self.highest1:,} ({self.highest1User})', inline=True)
        .add_field(f'{self.option2} (Blue) {self.percentage2:.0f}%', f'Total Bets: 🪙 {self.total2:,}\nPayout: 💸 {self.payout2:.2f}\nParticipants: 👥 {len(self.participant2):,}\nHighest Bet: 🪙 {self.highest2:,} ({self.highest2User})', inline=True)
        )
        await self.message.edit(embed, components=[])
        self.cursor.close()
        self.db.close()
    
    async def view_check(self, ctx: miru.Context) -> bool:
        return True

class StopBet(miru.View):
    def __init__(self, author: hikari.User) -> None:
        self.author = author
    
    @miru.button(label='Close', style=hikari.ButtonStyle.DANGER, row=1)
    async def close(self, ctx: miru.Context):
        self.stop()
    
    async def view_check(self, ctx: miru.Context) -> bool:
        return ctx.user.id == self.author.id

class StopBet(miru.Button):
    def __init__(self, author: hikari.User) -> None:
        super().__init__(label='Close', style=hikari.ButtonStyle.DANGER, row=1)
        self.author = author
        
    async def callback(self, ctx: miru.Context) -> None:
        if ctx.user.id == self.author.id:
            self.view.stop()

class WhoWinsView(miru.View):
    def __init__(self, author: hikari.User) -> None:
        super().__init__(timeout=None)
        self.author = author

    async def view_check(self, ctx: miru.Context) -> bool:
        return ctx.user.id == self.author.id

class GreenWinButton(miru.Button):
    def __init__(self, name: str, bets: dict, losers: dict, payout: float, participants: int, highestBet: hikari.User) -> None:
        super().__init__(label=name, style=hikari.ButtonStyle.SUCCESS)
        self.name = name
        self.bets = bets
        self.losers = losers
        self.payout = payout
        self.participants = participants
        self.highestBet = highestBet
        
        self.db = sqlite3.connect('database.sqlite')
        self.cursor = self.db.cursor()
    
    async def callback(self, ctx: miru.Context) -> None:
        if len(self.participants) > 0:
            embed = (hikari.Embed(title=f'{self.name} Won!', description=f'🪙 {(self.bets.get(self.highestBet.id) * self.payout):,.0f} go to {self.highestBet} and {(len(self.participants) - 1):,} others.',  color=get_setting('embed_color')))
            embed.set_thumbnail(self.highestBet.avatar_url)
            
            for user in self.bets:
                self.cursor.execute(f'SELECT balance, total FROM database WHERE user_id = {user}') # moves cursor to user's balance and total from database
                bal = self.cursor.fetchone() # grabs the value of user's balance
                
                try: # just in case for errors
                    balance = bal[0] # balance SHOULD be at index 0
                    total = bal[1] # total SHOULD be at index 1
                except:
                    balance = 0
                    total = 0
                
                sql = ('UPDATE database SET balance = ?, total = ? WHERE user_id = ?') # update user's new balance and total in database
                val = (balance + round(self.payout * self.bets.get(user)), total + round(self.payout * self.bets.get(user)), user)

                self.cursor.execute(sql, val) # executes the instructions
                self.db.commit() # saves changes 
            
            for user in self.losers:
                self.cursor.execute(f'SELECT loss FROM database WHERE user_id = {user}') # moves cursor to user's loss from database
                val = self.cursor.fetchone() # grabs the value of user's total loss
                
                try: # just in case for errors
                    loss = val[0] # loss SHOULD be at index 0
                except:
                    loss = 0
                
                sql = ('UPDATE database SET loss = ? WHERE user_id = ?') # update user's new loss in database
                val = (loss + self.losers.get(user), user)

                self.cursor.execute(sql, val) # executes the instructions
                self.db.commit() # saves changes
            
            self.cursor.close()
            self.db.close()  
        else:
            embed = (hikari.Embed(title=f'{self.name} Won!', description=f'Unfortunately, no one will get paid out...',  color=get_setting('embed_color')))
        await ctx.message.respond(embed, reply=False)   
        self.view.stop()

class BlueWinButton(miru.Button):
    def __init__(self, name: str, bets: dict, losers: dict,payout: float, participants: int, highestBet: hikari.User) -> None:
        super().__init__(label=name, style=hikari.ButtonStyle.PRIMARY)
        self.name = name
        self.bets = bets
        self.losers = losers
        self.payout = payout
        self.participants = participants
        self.highestBet = highestBet
        
        self.db = sqlite3.connect('database.sqlite')
        self.cursor = self.db.cursor()
    
    async def callback(self, ctx: miru.Context) -> None:
        if len(self.participants) > 0:
            embed = (hikari.Embed(title=f'{self.name} Won!', description=f'🪙 {(self.bets.get(self.highestBet.id) * self.payout):,.0f} go to {self.highestBet} and {(len(self.participants) - 1):,} others.',  color=get_setting('embed_color')))
            embed.set_thumbnail(self.highestBet.avatar_url)
            
            for user in self.bets:
                self.cursor.execute(f'SELECT balance, total FROM database WHERE user_id = {user}') # moves cursor to user's balance and total from database
                bal = self.cursor.fetchone() # grabs the value of user's balance
                
                try: # just in case for errors
                    balance = bal[0] # balance SHOULD be at index 0
                    total = bal[1] # total SHOULD be at index 1
                except:
                    balance = 0
                    total = 0
                
                sql = ('UPDATE database SET balance = ?, total = ? WHERE user_id = ?') # update user's new balance and total in database
                val = (balance + round(self.payout * self.bets.get(user)), total + round(self.payout * self.bets.get(user)), user)

                self.cursor.execute(sql, val) # executes the instructions
                self.db.commit() # saves changes 
            
            for user in self.losers:
                self.cursor.execute(f'SELECT loss FROM database WHERE user_id = {user}') # moves cursor to user's loss from database
                val = self.cursor.fetchone() # grabs the value of user's total loss
                
                try: # just in case for errors
                    loss = val[0] # loss SHOULD be at index 0
                except:
                    loss = 0
                
                sql = ('UPDATE database SET loss = ? WHERE user_id = ?') # update user's new loss in database
                val = (loss + self.losers.get(user), user)

                self.cursor.execute(sql, val) # executes the instructions
                self.db.commit() # saves changes
            
            self.cursor.close()
            self.db.close()  
        else:
            embed = (hikari.Embed(title=f'{self.name} Won!', description=f'Unfortunately, no one will get paid out...',  color=get_setting('embed_color')))
        
        await ctx.message.respond(embed, reply=False) 
        self.view.stop()

class RefundButton(miru.Button):
    def __init__(self, greenBets: dict, blueBets: dict) -> None:
        super().__init__(label='Refund', style=hikari.ButtonStyle.DANGER)
        self.greenBets = greenBets
        self.blueBets = blueBets

    async def callback(self, ctx: miru.Context) -> None:
        for user in self.greenBets:
            add_money(user, self.greenBets.get(user), False)
            
        for user in self.blueBets:
            add_money(user, self.blueBets.get(user), False)
        
        embed = hikari.Embed(description='All bets has been refunded!', color=get_setting('embed_color'))
        await ctx.message.respond(embed, reply=False) 
        self.view.stop()

@admin.child
@lightbulb.option('option2', 'The second option a member can bet on.', type=str, required=True)
@lightbulb.option('option1', 'The first option a member can bet on.', type=str, required=True)
@lightbulb.command('bet', 'Start a live interactive bet!', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def bet(ctx: lightbulb.Context, option1: str, option2: str) -> None:
    author = ctx.author
    view = BetView(author, option1, option2)
    view.add_item(StopBet(author))
    
    embed = (hikari.Embed(title="Bets are open!", color=get_setting('embed_color'))
        .add_field(f'{option1} (Green) 50%', 'Total Coins: 🪙 0\nPayout: 💸 0.00\nParticipants: 👥 0\nHighest Bet: 🪙 0 (N/A)', inline=True)
        .add_field(f'{option2} (Blue) 50%', 'Total Coins: 🪙 0\nPayout: 💸 0.00\nParticipants: 👥 0\nHighest Bet: 🪙 0 (N/A)', inline=True)
    )
    
    message = await ctx.respond(embed, components=view.build())
    message = await message
    
    await view.start(message)
    await view.wait()
    
    greenLabel = view.option1
    blueLabel = view.option2
    
    greenBets = view.bet1
    blueBets = view.bet2
    
    greenPayout = view.payout1
    bluePayout = view.payout2
    
    greenParticipants = view.participant1
    blueParticipants = view.participant2
    
    greenHighestBet = view.highest1User
    blueHighestBet = view.highest2User
    
    embed = (hikari.Embed(title="Bets are closed!", color=get_setting('embed_color'))
    .add_field(f'{view.option1} (Green) {view.percentage1:.0f}%', f'Total Coins: 🪙 {view.total1:,}\nPayout: 💸 {view.payout1:.2f}\nParticipants: 👥 {len(view.participant1):,}\nHighest Bet: 🪙 {view.highest1:,} ({view.highest1User})', inline=True)
    .add_field(f'{view.option2} (Blue) {view.percentage2:.0f}%', f'Total Coins: 🪙 {view.total2:,}\nPayout: 💸 {view.payout2:.2f}\nParticipants: 👥 {len(view.participant2):,}\nHighest Bet: 🪙 {view.highest2:,} ({view.highest2User})', inline=True)
    )
        
    await ctx.edit_last_response(embed, components=[])
    
    view = WhoWinsView(author)
    view.add_item(GreenWinButton(greenLabel, greenBets, blueBets, greenPayout, greenParticipants, greenHighestBet))
    view.add_item(BlueWinButton(blueLabel, blueBets, greenBets, bluePayout, blueParticipants, blueHighestBet))
    view.add_item(RefundButton(greenBets, blueBets))
    
    embed = (hikari.Embed(title="DO NOT CLOSE THIS MENU", description='Choose which color has won or refund all bets.', color=get_setting('embed_color')))
    
    message = await ctx.respond(embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)
    message = await message
    
    await view.start(message)

## Set Balance Command ##

@admin.child
@lightbulb.option('amount', 'The amount that will be set to.', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('eco-set', "Set a server member's wallet to a specific amount.", pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def set_balance(ctx: lightbulb.Context, user: hikari.User, amount: int):
    if user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description='You are not allowed to set money to this user!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif set_money(user.id, amount):
        embed = (hikari.Embed(description=f"You set {user.username}'s wallet to 🪙 {amount:,}", color=get_setting('embed_color')))
        await ctx.respond(embed)
    return

## Add Balance Command ##

@admin.child
@lightbulb.option('update', 'This will update net gain.', type=bool, required=True)
@lightbulb.option('amount', 'The amount that will be added to.', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('eco-add', "Add coins to a server member's wallet.", pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def add_balance(ctx: lightbulb.Context, user: hikari.User, amount: int, update: bool):
    if user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description='You are not allowed to add money to this user!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif add_money(user.id, amount, update):
        embed = (hikari.Embed(description=f"You added 🪙 {amount:,} to {user.username}'s wallet!", color=get_setting('embed_color')))
        await ctx.respond(embed)
    return
    

## Take Balance Command ##

@admin.child
@lightbulb.option('update', 'This will update net loss.', type=bool, required=True)
@lightbulb.option('amount', 'The amount that will be removed from.', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('eco-take', "Remove coins to a server member's wallet.", pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def take_balance(ctx: lightbulb.Context, user: hikari.User, amount: int, update: bool):
    if user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description='You are not allowed to take money from this user!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif remove_money(user.id, amount, update):
        embed = (hikari.Embed(description=f"You took 🪙 {amount:,} from {user.username}'s wallet!", color=get_setting('embed_color')))
        await ctx.respond(embed)
    else:
        embed = (hikari.Embed(description=f"That amount exceeds {user.username}'s wallet!", color=get_setting('embed_error_color')))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    return

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

## Add as a plugin ##

def load(bot):
    bot.add_plugin(plugin)

def user_had_bets(bet: dict, user: hikari.User):
    if bet.get(user.id) == None:
        return False
    return True

def get_bet(bets: dict):
        values = bets.values()
        values = list(values)
        return values[0] if len(values) > 0 else 1

def add_bet(bets: dict, user: hikari.User, amount: int):
    return bets[user.id] + amount

def remove_bet(bets: dict, user: hikari.User, amount: int):
    return bets[user.id] - amount