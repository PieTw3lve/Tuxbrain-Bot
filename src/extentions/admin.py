import hikari
import lightbulb
import miru
import asyncio

from datetime import datetime, timezone, timedelta
from bot import get_setting, write_setting, verify_user
from .economy import set_money, add_money, add_ticket, remove_money, remove_ticket, add_loss

plugin = lightbulb.Plugin('Admin')

## Admin Subcommand ##

@plugin.command
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
        
        embed = hikari.Embed(description='You already voted!', color=get_setting('embed_error_color'))
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
    
    embed = hikari.Embed(title='Are you sure you want to continue the purge operation?', description='**__WARNING:__** This Action is irreversible!', color=get_setting('embed_color'))
    message = await ctx.respond(embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)
    
    await view.start(message)
    await view.wait()

    if hasattr(view, "accepted"):
        if view.accepted is True:
            await purge_messages(ctx, amount, channel)
        elif view.accepted is False:
            await ctx.edit_last_response(hikari.Embed(title='Cancelled', description=f'Purge operation has been cancelled.', color=get_setting('embed_error_color')), components=[])
    else:
        await ctx.edit_last_response(hikari.Embed(title='Timed out', description=f'Purge operation has been cancelled due to inactivity...', color=get_setting('embed_error_color')), components=[])

async def purge_messages(ctx: lightbulb.Context, amount: int, channel: hikari.Snowflakeish) -> None:
    iterator = (
                ctx.bot.rest.fetch_messages(channel)
                .limit(amount)
                .take_while(lambda msg: (datetime.now(timezone.utc) - msg.created_at) < timedelta(days=14))
            )
    if iterator:
        async for messages in iterator.chunk(100):
            await ctx.bot.rest.delete_messages(channel, messages)
        await ctx.edit_last_response(hikari.Embed(title='Success', description=f'Messages has been sucessfully deleted.', color=get_setting('embed_success_color')), components=[])
    else:
        await ctx.edit_last_response(title='Error', description=f'Could not find any messages younger than 14 days!', color=get_setting('embed_error_color'), components=[])

## Bet Command ##

betViewEvents = {}

class BetView(miru.View):
    def __init__(self, task: asyncio.Task, author: hikari.User, embed: hikari.Embed, blue: str, green: str, timer: int) -> None:
        super().__init__(timeout=None, autodefer=True)
        self.task = task
        self.author = author
        self.embed = embed
        self.blueName = blue
        self.greenName = green
        self.blueTeam = {}
        self.greenTeam = {}
    
    @miru.button(label='Bet Blue', style=hikari.ButtonStyle.PRIMARY)
    async def blue(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        modal = BettingView(self.blueTeam, self.greenTeam, 0)
        userID = ctx.user.id
        await ctx.respond_with_modal(modal)

        await modal.wait()

        if not modal.valid:
            return
        else:
            # If the user is not in any team, add them to the blue team
            if userID in self.blueTeam.keys():
                self.blueTeam[userID] += modal.amount
            else:
                self.blueTeam.update({ctx.user.id: modal.amount})
        
        await BetView.update_view(self)
             
    @miru.button(label='Bet Green', style=hikari.ButtonStyle.SUCCESS)
    async def green(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        modal = BettingView(self.blueTeam, self.greenTeam, 1)
        userID = str(ctx.user.id)
        await ctx.respond_with_modal(modal)

        await modal.wait()

        if not modal.valid:
            return
        else:
            # If the user is not in any team, add them to the green team
            if userID in self.greenTeam.keys():
                self.greenTeam[userID] += modal.amount
            else:
                self.greenTeam.update({ctx.user.id: modal.amount})
        
        await BetView.update_view(self)
    
    @miru.button(label='Force Close', style=hikari.ButtonStyle.DANGER)
    async def close(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        if ctx.user.id == self.author.id:
            self.task.cancel()
    
    async def update_view(self) -> None:
        self.bTotal = sum(self.blueTeam.values())
        self.gTotal = sum(self.greenTeam.values())
        self.bPercentage = 100 * (self.bTotal/(self.bTotal + self.gTotal))
        self.gPercentage = 100 * (self.gTotal/(self.gTotal + self.bTotal))
        self.bHighID = max(self.blueTeam, key=lambda k: self.blueTeam[k]) if len(self.blueTeam) > 0 else None
        self.gHighID = max(self.greenTeam, key=lambda k: self.greenTeam[k]) if len(self.greenTeam) > 0 else None
        self.bHighBet = self.blueTeam[self.bHighID] if len(self.blueTeam) > 0 else 0
        self.gHighBet = self.greenTeam[self.gHighID] if len(self.greenTeam) > 0 else 0
        self.bPayout = (self.bHighBet + (self.bHighBet/self.bTotal) * self.gTotal)/self.bHighBet if len(self.blueTeam) > 0 else 0
        self.gPayout = (self.gHighBet + (self.gHighBet/self.gTotal) * self.bTotal)/self.gHighBet if len(self.greenTeam) > 0 else 0
        self.bParticipants = len(self.blueTeam) if len(self.blueTeam) > 0 else 0
        self.gParticipants = len(self.greenTeam) if len(self.greenTeam) > 0 else 0

        self.embed.edit_field(0, f'{self.blueName} (Blue) {self.bPercentage:.0f}%', f'Total Coins: 🪙 {self.bTotal:,}\nPayout: 💸 {self.bPayout:.2f}\nParticipants: 👥 {self.bParticipants:,}\nHighest Bet: 🪙 {self.bHighBet:,} (<@{self.bHighID}>)')
        self.embed.edit_field(1, f'{self.greenName} (Green) {self.gPercentage:.0f}%', f'Total Coins: 🪙 {self.gTotal:,}\nPayout: 💸 {self.gPayout:.2f}\nParticipants: 👥 {self.gParticipants:,}\nHighest Bet: 🪙 {self.gHighBet:,} (<@{self.gHighID}>)')
        await self.message.edit(self.embed)
    
    def get_blue_overview(self, amount: int) -> str:
        sortedTeam = sorted(self.blueTeam, key=lambda k: self.blueTeam[k], reverse=True)
        rankings = ''
        for i, key in enumerate(sortedTeam):
            if i >= amount:
                break
            rankings += f'\n> {i:,}. <@{key}> 🪙 {self.blueTeam[key]:,}'
        return rankings
    
    def get_green_overview(self, amount: int) -> str:
        sortedTeam = sorted(self.greenTeam, key=lambda k: self.greenTeam[k], reverse=True)
        rankings = ''
        for i, key in enumerate(sortedTeam):
            if i >= amount:
                break
            rankings += f'\n> {i:,}. <@{key}> 🪙 {self.greenTeam[key]:,}'
        return rankings

class ResultView(miru.View):
    def __init__(self, author: hikari.User, betView: BetView) -> None:
        super().__init__(timeout=None, autodefer=True)
        self.author = author
        self.betView = betView
    
    @miru.text_select(
        placeholder='Select Winning Team',
        options=[
            miru.SelectOption(label=f'Blue', value='blue'),
            miru.SelectOption(label='Green', value='green'),
            miru.SelectOption(label='Refund', value='refund'),
        ],
        row=1
    )
    async def select_winner(self, select: miru.TextSelect, ctx: miru.Context):
        option = select.values[0]
        await ctx.edit_response(components=[])
        self.stop()

        match option:
            case 'blue':
                for userID in self.betView.blueTeam.keys():
                    add_money(userID, round(self.betView.blueTeam[userID] * self.betView.bPayout), True)
                for userID in self.betView.greenTeam.keys():
                    add_loss(userID, self.betView.greenTeam[userID])
                if len(self.betView.blueTeam) > 0:
                    user = await ctx.app.rest.fetch_user(self.betView.bHighID)
                    embed = (hikari.Embed(title=f'{self.betView.blueName} Won!', description=f'🪙 {(self.betView.bHighBet * self.betView.bPayout):,.0f} go to <@{self.betView.bHighID}> and {(self.betView.bParticipants) - 1:,} others.\n{self.betView.get_blue_overview(10)}\n‍',  color=get_setting('embed_color')))
                    embed.set_thumbnail(user.avatar_url)
                else:
                    embed = (hikari.Embed(title=f'{self.betView.blueName} Won!', description=f'Unfortunately, no one will get paid out...',  color=get_setting('embed_color')))
            case 'green':
                for userID in self.betView.greenTeam.keys():
                    add_money(userID, round(self.betView.greenTeam[userID] * self.betView.gPayout), True)
                for userID in self.betView.blueTeam.keys():
                    add_loss(userID, self.betView.blueTeam[userID])
                if len(self.betView.greenTeam) > 0:
                    user = await ctx.app.rest.fetch_user(self.betView.gHighID)
                    embed = (hikari.Embed(title=f'{self.betView.greenName} Won!', description=f'🪙 {(self.betView.gHighBet * self.betView.gPayout):,.0f} go to <@{self.betView.gHighID}> and {(self.betView.gParticipants - 1):,} others.\n{self.betView.get_green_overview(10)}\n‍',  color=get_setting('embed_color')))
                    embed.set_thumbnail(user.avatar_url) 
                else:
                    embed = (hikari.Embed(title=f'{self.betView.greenName} Won!', description=f'Unfortunately, no one will get paid out...',  color=get_setting('embed_color')))
            case 'refund':
                for userID in self.betView.blueTeam.keys():
                    add_money(userID, self.betView.blueTeam[userID], False)
                for userID in self.betView.greenTeam.keys():
                    add_money(userID, self.betView.greenTeam[userID], False)
                embed = hikari.Embed(title='Bets has been canceled!', description='All bets has been refunded.', color=get_setting('embed_color'))
        
        embed.set_footer(text="The players' balances have been updated")
        await self.message.respond(embed, reply=True)
    
    async def view_check(self, ctx: miru.Context) -> bool:
        return ctx.user.id == self.author.id

class BettingView(miru.Modal):
    amount = miru.TextInput(label='Bet Amount', placeholder='100', style=hikari.TextInputStyle.SHORT, required=True)

    def __init__(self, blueTeam: dict, greenTeam: dict, team: int) -> None:
        super().__init__(title='Add Bet', timeout=10)
        self.blueTeam = blueTeam
        self.greenTeam = greenTeam
        self.team = team
        self.valid = False
    
    async def callback(self, ctx: miru.ModalContext) -> None:
        userID = ctx.user.id
        entry = self.blueTeam.get(userID, None) if not self.team else self.greenTeam.get(userID, None)
        try:
            self.amount = int(self.amount.value)
            if verify_user(ctx.user) == None: # if user has never been register
                embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
                return
            elif remove_money(userID, self.amount, False) == False:
                embed = hikari.Embed(title='Bet Error', description='You do not have enough money!', color=get_setting('embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
                self.stop()
                return
            elif userID in self.greenTeam.keys() and not self.team:
                embed = hikari.Embed(description="You can only bet on one team!", color=get_setting('embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
                self.stop()
                return
            elif userID in self.blueTeam.keys() and self.team:
                embed = hikari.Embed(description="You can only bet on one team!", color=get_setting('embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
                self.stop()
                return
            else:
                embed = hikari.Embed(title='Success', description=f'You added 🪙 {self.amount:,} to {"Blue" if not self.team else "Green"}! \nYour total is 🪙 {entry + self.amount if entry is not None else self.amount:,}.', color=get_setting('embed_success_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
                self.valid = True
                self.stop()
                return
        except:
            embed = hikari.Embed(title='Bet Error', description='Amount is not a valid number!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
            self.stop()
            return

@admin.child
@lightbulb.option('timer', 'How long users have to bet on the outcome (in seconds).', type=int, min_value=5, required=True)
@lightbulb.option('green', 'Outcome 2, like "No"', type=str, required=True)
@lightbulb.option('blue', 'Outcome 1, like "Yes"', type=str, required=True)
@lightbulb.option('name', 'What users will bet, like "Will I win five games in a row?"', type=str, required=True)
@lightbulb.command('bet', 'Start a live interactive bet!', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def bet(ctx: lightbulb.Context, blue: str, name: str, green: str, timer: int) -> None:
    embed = hikari.Embed(title=f'{name} (Open)', description=f'Submissions will close in {format_seconds(timer)}.', color=get_setting('embed_color'), timestamp=datetime.now().astimezone())
    embed.add_field(name=f'{blue} (Blue) 50%', value='Total Coins: 🪙 0\nPayout: 💸 0.00\nParticipants: 👥 0\nHighest Bet: 🪙 0 (<@None>)', inline=True)
    embed.add_field(name=f'{green} (Green) 50%', value='Total Coins: 🪙 0\nPayout: 💸 0.00\nParticipants: 👥 0\nHighest Bet: 🪙 0 (<@None>)', inline=True)
    embed.set_footer(text=f'Requested by {ctx.author.global_name}', icon=ctx.author.display_avatar_url)

    event = asyncio.Event()
    task = asyncio.create_task(cancel_sleep(event, timer))  # Start the cancel_sleep task

    view = BetView(task, ctx.author, embed, blue, green, timer)
    message = await ctx.respond(embed, components=view.build())
    
    await view.start(message)

    # Update timer real time
    while not event.is_set():
        remaining = event.end_time - datetime.now().astimezone()
        embed.description = f'Submissions will close in {format_seconds(int(remaining.total_seconds()))}.'
        await message.edit(embed=embed)
        await asyncio.sleep(10)  # Update the timer every 60 seconds
    
    view.stop()
    view = ResultView(ctx.user, view)
    embed.title = f'{name} (Closed)'
    embed.description = f'Submissions have ended'
    message = await ctx.edit_last_response(embed, components=view.build())
    await view.start(message)

async def cancel_sleep(event: asyncio.Event, timer: int) -> None:
    try:
        event.end_time = datetime.now().astimezone() + timedelta(seconds=timer)
        while datetime.now().astimezone() < event.end_time:
            remaining_time = (event.end_time - datetime.now().astimezone()).total_seconds()
            await asyncio.sleep(min(1, remaining_time))  # Sleep for a minimum of 60 seconds or until the timer expires
        event.set()  # Set the event when the timer expires
    except asyncio.CancelledError:
        event.set()  # Set the event when the sleep is canceled

def format_seconds(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    time = []

    if days:
        time.append(f"{days} day{'s' if days > 1 else ''}")
        time.append(f"{hours} hour{'s' if hours > 1 else ''}")
    elif hours:
        time.append(f"{hours} hour{'s' if hours > 1 else ''}")
        time.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    elif minutes:
        time.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        time.append(f"{seconds} second{'s' if seconds > 1 else ''}")
    else:
        time.append(f"{seconds} second{'s' if seconds > 1 else ''}")

    return " and ".join(time)

## Set Balance Command ##

@admin.child
@lightbulb.option('amount', 'The amount that will be set to.', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('eco-set', "Set a server member's wallet to a specific amount.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def set_balance(ctx: lightbulb.Context, user: hikari.User, amount: int):
    if user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description='You are not allowed to set money to this user!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif set_money(user.id, amount):
        embed = (hikari.Embed(description=f"You set {user.global_name}'s wallet to 🪙 {amount:,}", color=get_setting('embed_color')))
        await ctx.respond(embed)
    return

## Add Balance Command ##

@admin.child
@lightbulb.option('update', 'This will update net gain.', type=bool, required=True)
@lightbulb.option('amount', 'The amount that will be added to.', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('eco-add', "Add coins to a server member's wallet.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def add_balance(ctx: lightbulb.Context, user: hikari.User, amount: int, update: bool):
    if user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description='You are not allowed to add money to this user!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif add_money(user.id, amount, update):
        embed = (hikari.Embed(description=f"You added 🪙 {amount:,} to {user.global_name}'s wallet!", color=get_setting('embed_color')))
        await ctx.respond(embed)
    return

## Add Ticket Command ##

@admin.child
@lightbulb.option('amount', 'The amount that will be added to.', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('eco-add-ticket', "Add tickets to a server member's wallet.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def add_balance(ctx: lightbulb.Context, user: hikari.User, amount: int):
    if user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description='You are not allowed to add tickets to this user!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif add_ticket(user.id, amount):
        embed = (hikari.Embed(description=f"You added {amount:,} 🎟️ to {user.global_name}'s wallet!", color=get_setting('embed_color')))
        await ctx.respond(embed)
    return
    

## Take Balance Command ##

@admin.child
@lightbulb.option('update', 'This will update net loss.', type=bool, required=True)
@lightbulb.option('amount', 'The amount that will be removed from.', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('eco-take', "Remove coins from a server member's wallet.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def take_balance(ctx: lightbulb.Context, user: hikari.User, amount: int, update: bool):
    if user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description='You are not allowed to take money from this user!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif remove_money(user.id, amount, update):
        embed = (hikari.Embed(description=f"You took 🪙 {amount:,} from {user.global_name}'s wallet!", color=get_setting('embed_color')))
        await ctx.respond(embed)
    else:
        embed = (hikari.Embed(description=f"That amount exceeds {user.global_name}'s wallet!", color=get_setting('embed_error_color')))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    return

## Take Ticket Command ##

@admin.child
@lightbulb.option('amount', 'The amount that will be removed from.', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('eco-take-ticket', "Remove tickets from a server member's wallet.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def take_balance(ctx: lightbulb.Context, user: hikari.User, amount: int, update: bool):
    if user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description='You are not allowed to take money from this user!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif remove_ticket(user.id, amount):
        embed = (hikari.Embed(description=f"You took {amount:,} 🎟️ from {user.global_name}'s wallet!", color=get_setting('embed_color')))
        await ctx.respond(embed)
    else:
        embed = (hikari.Embed(description=f"That amount exceeds {user.global_name}'s wallet!", color=get_setting('embed_error_color')))
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