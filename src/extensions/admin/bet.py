from enum import Enum
import uuid
import hikari
import lightbulb
import asyncio

from datetime import datetime, timedelta
from bot import get_setting, verify_user, register_user
from extensions.general.error import format_seconds
from utils.economy.manager import EconomyManager

loader = lightbulb.Loader()

economy = EconomyManager()

betViewEvents = {}

class Team(Enum):
    BLUE = 1
    GREEN = 2
    NONE = 3

class BettingModal(lightbulb.components.Modal):
    def __init__(self, blueTeam: dict, greenTeam: dict, team: int) -> None:
        self.coins = self.add_short_text_input(label="Bet Amount", placeholder="100", required=True)
        self.blueTeam = blueTeam
        self.greenTeam = greenTeam
        self.team = team
        self.valid = False
    
    async def on_submit(self, ctx: lightbulb.components.ModalContext):
        userID = ctx.user.id
        entry = self.blueTeam.get(userID, None) if not self.team else self.greenTeam.get(userID, None)
        try:
            self.coins = int(ctx.value_for(self.coins))
            if verify_user(ctx.user) == None:
                register_user(ctx.user)
            if self.coins < 1:
                embed = hikari.Embed(title="Bet Error", description="Amount is not a valid number!", color=get_setting("general", "embed_error_color"))
                return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            elif economy.remove_money(userID, self.coins, False) == False:
                embed = hikari.Embed(title="Bet Error", description="You do not have enough money!", color=get_setting("general", "embed_error_color"))
                return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            elif userID in self.greenTeam.keys() and not self.team:
                embed = hikari.Embed(description="You can only bet on one team!", color=get_setting("general", "embed_error_color"))
                return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            elif userID in self.blueTeam.keys() and self.team:
                embed = hikari.Embed(description="You can only bet on one team!", color=get_setting("general", "embed_error_color"))
                return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            else:
                embed = hikari.Embed(title="Success", description=f"You added {self.coins:,} 🪙 to {'Blue' if not self.team else 'Green'} for a total of {entry + self.coins if entry is not None else self.coins:,} 🪙!", color=get_setting("general", "embed_success_color"))
                self.valid = True
                return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        except:
            embed = hikari.Embed(title="Bet Error", description="Amount is not a valid number!", color=get_setting("general", "embed_error_color"))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

class BetMenu(lightbulb.components.Menu):
    def __init__(self, task: asyncio.Task, author: hikari.User, embed: hikari.Embed, blue: str, green: str, timer: int) -> None:
        self.blueButton = self.add_interactive_button(style=hikari.ButtonStyle.PRIMARY, label="Bet Blue", on_press=self.on_blue)
        self.greenButton = self.add_interactive_button(style=hikari.ButtonStyle.SUCCESS, label="Bet Green", on_press=self.on_green)
        self.close = self.add_interactive_button(style=hikari.ButtonStyle.DANGER, label="Force Close", on_press=self.on_close)
        self.task = task
        self.author = author
        self.embed = embed
        self.blueName = blue
        self.greenName = green
        self.blueTeam = {}
        self.greenTeam = {}
    
    async def on_blue(self, ctx: lightbulb.components.MenuContext) -> None:
        modal = BettingModal(self.blueTeam, self.greenTeam, 0)
        userID = ctx.user.id

        await ctx.respond_with_modal("Add Bet", cid := str(uuid.uuid4()), components=modal)

        try:
            await modal.attach(ctx.client, cid, timeout=10)
        except asyncio.TimeoutError:
            pass

        if not modal.valid:
            return
        else:
            # If the user is not in any team, add them to the blue team
            if userID in self.blueTeam.keys():
                self.blueTeam[userID] += modal.coins
            else:
                self.blueTeam.update({ctx.user.id: modal.coins})
        
        await self.update_view(ctx)

    async def on_green(self, ctx: lightbulb.components.MenuContext) -> None:
        modal = BettingModal(self.blueTeam, self.greenTeam, 1)
        userID = str(ctx.user.id)
        
        await ctx.respond_with_modal("Add Bet", cid := str(uuid.uuid4()), components=modal)

        try:
            await modal.attach(ctx.client, cid, timeout=10)
        except asyncio.TimeoutError:
            pass

        if not modal.valid:
            return
        else:
            # If the user is not in any team, add them to the green team
            if userID in self.greenTeam.keys():
                self.greenTeam[userID] += modal.coins
            else:
                self.greenTeam.update({ctx.user.id: modal.coins})
        
        await self.update_view(ctx)
    
    async def on_close(self, ctx: lightbulb.components.MenuContext) -> None:
        if ctx.user.id == self.author.id:
            self.task.cancel()
            ctx.stop_interacting()

    async def update_view(self, ctx: lightbulb.components.MenuContext) -> None:
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

        self.embed.edit_field(0, f"{self.blueName} (Blue) {self.bPercentage:.0f}%", f"Total Coins: {self.bTotal:,} 🪙\nPayout: 💸 {self.bPayout:.2f}\nParticipants: 👥 {self.bParticipants:,}\nHighest Bet: {self.bHighBet:,} 🪙 (<@{self.bHighID}>)")
        self.embed.edit_field(1, f"{self.greenName} (Green) {self.gPercentage:.0f}%", f"Total Coins: {self.gTotal:,} 🪙\nPayout: 💸 {self.gPayout:.2f}\nParticipants: 👥 {self.gParticipants:,}\nHighest Bet: {self.gHighBet:,} 🪙 (<@{self.gHighID}>)")
        await ctx.interaction.message.edit(self.embed)
    
    def get_blue_overview(self, amount: int) -> str:
        sortedTeam = sorted(self.blueTeam, key=lambda k: self.blueTeam[k], reverse=True)
        rankings = ""
        for i, key in enumerate(sortedTeam):
            if i >= amount:
                break
            rankings += f"\n> {i:,}. <@{key}> {self.blueTeam[key]:,} 🪙"
        return rankings
    
    def get_green_overview(self, amount: int) -> str:
        sortedTeam = sorted(self.greenTeam, key=lambda k: self.greenTeam[k], reverse=True)
        rankings = ""
        for i, key in enumerate(sortedTeam):
            if i >= amount:
                break
            rankings += f"\n> {i:,}. <@{key}> {self.greenTeam[key]:,} 🪙"
        return rankings
    
class ResultMenu(lightbulb.components.Menu):
    def __init__(self, author: hikari.User, betView: BetMenu) -> None:
        self.winnerSelect = self.add_text_select(
            placeholder="Select a winner",
            options=[
                lightbulb.components.TextSelectOption(label="Blue", value=Team.BLUE.value),
                lightbulb.components.TextSelectOption(label="Green", value=Team.GREEN.value),
                lightbulb.components.TextSelectOption(label="Refund", value=Team.NONE.value),
            ],
            on_select=self.on_select,
        )
        self.author = author
        self.betView = betView
    
    async def on_select(self, ctx: lightbulb.components.MenuContext):
        option = int(ctx.selected_values_for(self.winnerSelect)[0])
        ctx.stop_interacting()

        match option:
            case Team.BLUE.value:
                for userID in self.betView.blueTeam.keys():
                    economy.add_money(userID, round(self.betView.blueTeam[userID] * self.betView.bPayout), False)
                if len(self.betView.blueTeam) > 0:
                    user = await ctx.client.rest.fetch_user(self.betView.bHighID)
                    embed = (hikari.Embed(title=f"{self.betView.blueName} Won!", description=f"{(self.betView.bHighBet * self.betView.bPayout):,.0f} 🪙 goes to <@{self.betView.bHighID}> and {(self.betView.bParticipants) - 1:,} others.\n{self.betView.get_blue_overview(10)}\n‍",  color=get_setting("general", "embed_color")))
                    embed.set_thumbnail(user.display_avatar_url)
                else:
                    embed = (hikari.Embed(title=f"{self.betView.blueName} Won!", description=f"Unfortunately, no one will get paid out...",  color=get_setting("general", "embed_color")))
            case Team.GREEN.value:
                for userID in self.betView.greenTeam.keys():
                    economy.add_money(userID, round(self.betView.greenTeam[userID] * self.betView.gPayout), False)
                if len(self.betView.greenTeam) > 0:
                    user = await ctx.client.rest.fetch_user(self.betView.gHighID)
                    embed = (hikari.Embed(title=f"{self.betView.greenName} Won!", description=f"{(self.betView.gHighBet * self.betView.gPayout):,.0f} 🪙 goes to <@{self.betView.gHighID}> and {(self.betView.gParticipants - 1):,} others.\n{self.betView.get_green_overview(10)}\n‍",  color=get_setting("general", "embed_color")))
                    embed.set_thumbnail(user.display_avatar_url) 
                else:
                    embed = (hikari.Embed(title=f"{self.betView.greenName} Won!", description=f"Unfortunately, no one will get paid out...",  color=get_setting("general", "embed_color")))
            case Team.NONE.value:
                for userID in self.betView.blueTeam.keys():
                    economy.add_money(userID, self.betView.blueTeam[userID], False)
                for userID in self.betView.greenTeam.keys():
                    economy.add_money(userID, self.betView.greenTeam[userID], False)
                embed = hikari.Embed(title="Bets has been canceled!", description="All bets has been refunded.", color=get_setting("general", "embed_color"))
        
        embed.set_footer(text="The player balances have been updated")
        await ctx.interaction.create_initial_response(response_type=hikari.ResponseType.DEFERRED_MESSAGE_UPDATE, flags=hikari.MessageFlag.EPHEMERAL)
        await ctx.interaction.message.respond(embed, reply=True)
    
    async def predicate(self, ctx: lightbulb.components.MenuContext) -> bool:
        return ctx.user.id == self.author.id

@loader.command
class PredictionCommand(lightbulb.SlashCommand, name="prediction", description="Initiate a live interactive bet for users to participate in."):
    name: str = lightbulb.string("name", "What users will bet (e.g. \"Will I win five games in a row?\").")
    blue: str = lightbulb.string("blue", "Outcome 1 (e.g. \"Yes\").")
    green: str = lightbulb.string("green", "Outcome 2 (e.g. \"No\").")
    duration: int = lightbulb.integer("duration", "How long users have to bet on the outcome (in seconds).", min_value=5)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, bot: hikari.GatewayBot) -> None:
        embed = hikari.Embed(title=f"{self.name} (Open)", description=f"Submissions will close in {format_seconds(self.duration)}.", color=get_setting("general", "embed_color"), timestamp=datetime.now().astimezone())
        embed.add_field(name=f"{self.blue} (Blue) 50%", value="Total Coins: 0 🪙\nPayout: 💸 0.00\nParticipants: 👥 0\nHighest Bet: 0 🪙 (<@None>)", inline=True)
        embed.add_field(name=f"{self.green} (Green) 50%", value="Total Coins: 0 🪙\nPayout: 💸 0.00\nParticipants: 👥 0\nHighest Bet: 0 🪙 (<@None>)", inline=True)
        embed.set_footer(text=f"Requested by {ctx.user.global_name}", icon=ctx.user.display_avatar_url)

        event = asyncio.Event()
        task = asyncio.create_task(cancel_sleep(event, self.duration))  # Start the cancel_sleep task

        menu = BetMenu(task, ctx.user, embed, self.blue, self.green, self.duration)
        
        resp = await ctx.respond(embed, components=menu)

        menu.attach_persistent(ctx.client, timeout=None)

        # Update timer real time
        while not event.is_set():
            remaining = event.end_time - datetime.now().astimezone()
            embed.description = f"Submissions will close in {format_seconds(int(remaining.total_seconds()))}."
            await ctx.edit_response(resp, embed=embed)
            await asyncio.sleep(10)  # Update the timer every 60 seconds
        
        await ctx.edit_response(resp, components=[])

        menu = ResultMenu(ctx.user, menu)

        embed.title = f"{self.name} (Closed)"
        embed.description = f"Submissions have ended"
        
        await ctx.edit_response(resp, embed, components=menu)
        
        await menu.attach(ctx.client, timeout=None)

        await ctx.edit_response(resp, components=[])

async def cancel_sleep(event: asyncio.Event, timer: int) -> None:
    try:
        event.end_time = datetime.now().astimezone() + timedelta(seconds=timer)
        while datetime.now().astimezone() < event.end_time:
            remaining_time = (event.end_time - datetime.now().astimezone()).total_seconds()
            await asyncio.sleep(min(1, remaining_time))  # Sleep for a minimum of 60 seconds or until the timer expires
        event.set()  # Set the event when the timer expires
    except asyncio.CancelledError:
        event.set()  # Set the event when the sleep is canceled