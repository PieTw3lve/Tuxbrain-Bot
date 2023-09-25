import hikari
import lightbulb
import miru
import asyncio

from datetime import datetime, timedelta
from bot import DEFAULT_GUILD_ID, get_setting, verify_user
from .economy import set_money, set_ticket, add_money, remove_money, add_loss, add_ticket, remove_ticket
from .error import Error

plugin = lightbulb.Plugin('Guild', default_enabled_guilds=DEFAULT_GUILD_ID)


## Admin Economy Subcommands ##

@plugin.command
@lightbulb.app_command_permissions(perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False)
@lightbulb.command('admin-eco', 'Manage player economy.')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def admin_eco(ctx: lightbulb.Context) -> None:
    return

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
                    embed = (hikari.Embed(title=f'{self.betView.blueName} Won!', description=f'🪙 {(self.betView.bHighBet * self.betView.bPayout):,.0f} go to <@{self.betView.bHighID}> and {(self.betView.bParticipants) - 1:,} others.\n{self.betView.get_blue_overview(10)}\n‍',  color=get_setting('settings', 'embed_color')))
                    embed.set_thumbnail(user.avatar_url)
                else:
                    embed = (hikari.Embed(title=f'{self.betView.blueName} Won!', description=f'Unfortunately, no one will get paid out...',  color=get_setting('settings', 'embed_color')))
            case 'green':
                for userID in self.betView.greenTeam.keys():
                    add_money(userID, round(self.betView.greenTeam[userID] * self.betView.gPayout), True)
                for userID in self.betView.blueTeam.keys():
                    add_loss(userID, self.betView.blueTeam[userID])
                if len(self.betView.greenTeam) > 0:
                    user = await ctx.app.rest.fetch_user(self.betView.gHighID)
                    embed = (hikari.Embed(title=f'{self.betView.greenName} Won!', description=f'🪙 {(self.betView.gHighBet * self.betView.gPayout):,.0f} go to <@{self.betView.gHighID}> and {(self.betView.gParticipants - 1):,} others.\n{self.betView.get_green_overview(10)}\n‍',  color=get_setting('settings', 'embed_color')))
                    embed.set_thumbnail(user.avatar_url) 
                else:
                    embed = (hikari.Embed(title=f'{self.betView.greenName} Won!', description=f'Unfortunately, no one will get paid out...',  color=get_setting('settings', 'embed_color')))
            case 'refund':
                for userID in self.betView.blueTeam.keys():
                    add_money(userID, self.betView.blueTeam[userID], False)
                for userID in self.betView.greenTeam.keys():
                    add_money(userID, self.betView.greenTeam[userID], False)
                embed = hikari.Embed(title='Bets has been canceled!', description='All bets has been refunded.', color=get_setting('settings', 'embed_color'))
        
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
                embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('settings', 'embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
                return self.stop()
            elif self.amount < 1:
                embed = hikari.Embed(title='Bet Error', description='Amount is not a valid number!', color=get_setting('settings', 'embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
                return self.stop()
            elif remove_money(userID, self.amount, False) == False:
                embed = hikari.Embed(title='Bet Error', description='You do not have enough money!', color=get_setting('settings', 'embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
                return self.stop()
            elif userID in self.greenTeam.keys() and not self.team:
                embed = hikari.Embed(description="You can only bet on one team!", color=get_setting('settings', 'embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
                return self.stop()
            elif userID in self.blueTeam.keys() and self.team:
                embed = hikari.Embed(description="You can only bet on one team!", color=get_setting('settings', 'embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
                return self.stop()
            else:
                embed = hikari.Embed(title='Success', description=f'You added 🪙 {self.amount:,} to {"Blue" if not self.team else "Green"} for a total of 🪙 {entry + self.amount if entry is not None else self.amount:,}!', color=get_setting('settings', 'embed_success_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=30)
                self.valid = True
                return self.stop()
        except:
            embed = hikari.Embed(title='Bet Error', description='Amount is not a valid number!', color=get_setting('settings', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
            return self.stop()

@admin_eco.child
@lightbulb.option('timer', 'How long users have to bet on the outcome (in seconds).', type=int, min_value=5, required=True)
@lightbulb.option('green', 'Outcome 2, like "No"', type=str, required=True)
@lightbulb.option('blue', 'Outcome 1, like "Yes"', type=str, required=True)
@lightbulb.option('name', 'What users will bet, like "Will I win five games in a row?"', type=str, required=True)
@lightbulb.command('bet', 'Start a live interactive bet!', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def bet(ctx: lightbulb.Context, blue: str, name: str, green: str, timer: int) -> None:
    embed = hikari.Embed(title=f'{name} (Open)', description=f'Submissions will close in {Error().format_seconds(timer)}.', color=get_setting('settings', 'embed_color'), timestamp=datetime.now().astimezone())
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
        embed.description = f'Submissions will close in {Error().format_seconds(int(remaining.total_seconds()))}.'
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

## Set Balance Command ##

@admin_eco.child
@lightbulb.option('amount', 'The amount that will be set to.', type=int, min_value=0, max_value=None, required=True)
@lightbulb.option('currency', 'The currency type that will be set to.', type=str, choices=['Coins', 'Tickets'], required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('set', "Set a server member's wallet to a specific amount.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def set_balance(ctx: lightbulb.Context, user: hikari.User, currency: str, amount: int):
    if user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description='You are not allowed to set money to this user!', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif currency == 'Coins':
        set_money(user.id, amount)
        embed = (hikari.Embed(description=f"You set {user.global_name}'s money to 🪙 {amount:,}.", color=get_setting('settings', 'embed_color')))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif currency == 'Tickets':
        set_ticket(user.id, amount)
        embed = (hikari.Embed(description=f"You set {user.global_name}'s ticket amount to 🎟️ {amount:,}.", color=get_setting('settings', 'embed_color')))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    return

## Add Balance Command ##

@admin_eco.child
@lightbulb.option('update', 'This will update net gain.', type=bool, required=True)
@lightbulb.option('amount', 'The amount that will be added to.', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('add-money', "Add coins to a server member's wallet.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def add_balance(ctx: lightbulb.Context, user: hikari.User, amount: int, update: bool):
    if user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description='You are not allowed to add money to this user!', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif add_money(user.id, amount, update):
        embed = (hikari.Embed(description=f"You added 🪙 {amount:,} to {user.global_name}'s wallet!", color=get_setting('settings', 'embed_color')))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    return

## Add Ticket Command ##

@admin_eco.child
@lightbulb.option('amount', 'The amount that will be added to.', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('add-ticket', "Add tickets to a server member's wallet.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def add_tpass(ctx: lightbulb.Context, user: hikari.User, amount: int):
    if user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description='You are not allowed to add tickets to this user!', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif add_ticket(user.id, amount):
        embed = (hikari.Embed(description=f"You added {amount:,} 🎟️ to {user.global_name}'s wallet!", color=get_setting('settings', 'embed_color')))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    return

## Take Balance Command ##

@admin_eco.child
@lightbulb.option('update', 'This will update net loss.', type=bool, required=True)
@lightbulb.option('amount', 'The amount that will be removed from.', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('take-money', "Remove coins from a server member's wallet.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def take_money(ctx: lightbulb.Context, user: hikari.User, amount: int, update: bool):
    if user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description='You are not allowed to take money from this user!', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif remove_money(user.id, amount, update):
        embed = (hikari.Embed(description=f"You took 🪙 {amount:,} from {user.global_name}'s wallet!", color=get_setting('settings', 'embed_color')))
        await ctx.respond(embed)
    else:
        embed = (hikari.Embed(description=f"That amount exceeds {user.global_name}'s wallet!", color=get_setting('settings', 'embed_error_color')))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    return

## Take Ticket Command ##

@admin_eco.child
@lightbulb.option('amount', 'The amount that will be removed from.', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', "The user's wallet that will change.", type=hikari.User, required=True)
@lightbulb.command('take-ticket', "Remove tickets from a server member's wallet.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def take_ticket(ctx: lightbulb.Context, user: hikari.User, amount: int, update: bool):
    if user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description='You are not allowed to take money from this user!', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif remove_ticket(user.id, amount):
        embed = (hikari.Embed(description=f"You took {amount:,} 🎟️ from {user.global_name}'s wallet!", color=get_setting('settings', 'embed_color')))
        await ctx.respond(embed)
    else:
        embed = (hikari.Embed(description=f"That amount exceeds {user.global_name}'s wallet!", color=get_setting('settings', 'embed_error_color')))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    return

## Add as a plugin ##

def load(bot):
    bot.add_plugin(plugin)