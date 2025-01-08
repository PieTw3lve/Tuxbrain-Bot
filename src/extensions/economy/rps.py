import asyncio
import hikari
import lightbulb
import miru

from io import BytesIO
from PIL import Image, ImageChops, ImageDraw, ImageFont
import requests

from bot import get_setting
from utils.economy.manager import EconomyManager

plugin = lightbulb.Plugin('RPS')
economy = EconomyManager()

MENU_IMAGE_PATH = 'assets/img/economy/rps/background.png'
REQUEST_IMAGE_PATH = 'assets/img/economy/rps/request.png'
CANCELED_IMAGE_PATH = 'assets/img/economy/rps/canceled.png'
WIN_IMAGE_PATH = 'assets/img/economy/rps/win.png'
THINKING_IMAGE_PATH = 'assets/img/economy/rps/thinking.png'
SELECTED_IMAGE_PATH = 'assets/img/economy/rps/selected.png'
ROCK_IMAGE_PATH = 'assets/img/economy/rps/rock.png'
PAPER_IMAGE_PATH = 'assets/img/economy/rps/paper.png'
SCISSORS_IMAGE_PATH = 'assets/img/economy/rps/scissors.png'

class Player:
    def __init__(self, user: hikari.Member) -> None:
        self.user = user
        self.choice = None
        self.wins = 0

    def choose(self, choice: str) -> None:
        self.choice = choice

    def reset(self) -> None:
        self.choice = None

class AIPlayer(Player):
    def __init__(self, user: hikari.Member) -> None:
        super().__init__(user)

    def choose(self) -> None:
        import random
        self.choice = random.choice(['rock', 'paper', 'scissors'])

def circle(pfp: Image, size: tuple) -> Image:
    pfp = pfp.resize(size).convert("RGBA")
    bigsize = (pfp.size[0] * 3, pfp.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask) 
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(pfp.size)
    mask = ImageChops.darker(mask, pfp.split()[-1])
    pfp.putalpha(mask)
    return pfp

class DuelView(miru.View):
    def __init__(self, ctx: lightbulb.Context, embed: hikari.Embed, sender: hikari.Member, receiver: hikari.Member, bet: int, wins: int, timeout: int = 300) -> None:
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.embed = embed
        self.sender = sender
        self.receiver = receiver
        self.bet = bet
        self.wins = wins
    
    @miru.button(label='Accept', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def accept(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if economy.remove_money(self.receiver.id, self.bet, False) == False:
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        timeout = 60

        view = RPSView(self.ctx, self.embed, {self.sender.id: Player(self.sender), self.receiver.id: Player(self.receiver)}, self.bet, self.wins, timeout)
        
        self.embed.title = 'Round 1: Rock, Paper, Scissors!'
        self.embed.description = (
            f'Choose your weapon to duel!\n\n'
            f'> **Offering Bet**: {self.bet:,} 🪙\n'
            f'> **Payout Winnings**: {self.bet * 2:,} 🪙'
        )
        self.embed.set_image(view.display(hidden=True))
        self.embed.set_footer(text=f'You have {timeout:,.0f} seconds to choose an action!')
        
        await ctx.edit_response(self.embed, components=view.build())
        ctx.client.start_view(view)
        self.stop()
    
    @miru.button(label='Decline', style=hikari.ButtonStyle.DANGER, row=1)
    async def decline(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        economy.add_money(self.sender.id, self.bet, False)

        self.embed.title = 'Duel request declined!'
        self.embed.description = (
            f'<@{self.receiver.id}> has declined <@{self.sender.id}>\'s duel request!\n\n'
            f'> **Win Condition**: First to {self.wins:,} win(s).\n'
            f'> **Offering Bet**: {self.bet:,} 🪙\n'
            f'> **Payout Winnings**: {self.bet * 2:,} 🪙'
        )
        self.embed.color = get_setting('general', 'embed_error_color')
        self.embed.set_image(self.display(canceled=True))
        self.embed.set_footer(None)

        await ctx.edit_response(self.embed, components=[])
        self.stop()

    def display(self, canceled: bool = False) -> bytes:
        senderAvatar = Image.open(BytesIO(requests.get(self.sender.avatar_url).content)).convert('RGBA') if self.sender.avatar_url else Image.open(BytesIO(requests.get(self.sender.default_avatar_url).content)).convert('RGBA')
        receiverAvatar = Image.open(BytesIO(requests.get(self.receiver.avatar_url).content)).convert('RGBA') if self.receiver.avatar_url else Image.open(BytesIO(requests.get(self.receiver.default_avatar_url).content)).convert('RGBA')
        menu = Image.open(MENU_IMAGE_PATH).convert('RGBA')
        request = Image.open(REQUEST_IMAGE_PATH).convert('RGBA')

        senderAvatar = circle(senderAvatar, (96, 96))
        receiverAvatar = circle(receiverAvatar, (96, 96))

        menu.paste(request, (0, 0), request)
        menu.paste(senderAvatar, (172, 164), senderAvatar)
        menu.paste(receiverAvatar, (532, 164), receiverAvatar)

        draw = ImageDraw.Draw(menu)
        font = ImageFont.truetype('assets/font/ThaleahFat.ttf', size=72)
        draw.text((176 + senderAvatar.width // 2, 120), self.sender.display_name, font=font, fill=(255, 255, 255), anchor='mm', align='center')
        draw.text((536 + receiverAvatar.width // 2, 120), self.receiver.display_name, font=font, fill=(255, 255, 255), anchor='mm', align='center')

        if canceled:
            canceled = Image.open(CANCELED_IMAGE_PATH).convert('RGBA')
            menu.paste(canceled, (0, 0), canceled)

        with BytesIO() as a:
            menu.save(a, 'PNG')
            a.seek(0)
            return a.getvalue()
    
    async def on_timeout(self) -> None:
        economy.add_money(self.sender.id, self.bet, False)
        
        self.embed.title = 'Duel request timed out!'
        self.embed.description = (
            f'<@{self.sender.id}>\'s duel request to <@{self.receiver.id}> has timed out!\n\n'
            f'> **Win Condition**: First to {self.wins:,} win(s).\n'
            f'> **Offering Bet**: {self.bet:,} 🪙\n'
            f'> **Payout Winnings**: {self.bet * 2:,} 🪙'
        )
        self.embed.color = get_setting('general', 'embed_error_color')
        self.embed.set_image(self.display(canceled=True))
        self.embed.set_footer(None)
        
        await self.ctx.edit_last_response(self.embed, components=[])

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.receiver.id
        
class RPSView(miru.View):
    def __init__(self, ctx: lightbulb.Context, embed: hikari.Embed, players: dict[hikari.Snowflake, Player], bet: int, wins: int, timeout: int = 60) -> None:
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.embed = embed
        self.players = players
        self.bet = bet
        self.wins = wins
        self.rounds = 1

    @miru.button(label='Rock', emoji='🪨', style=hikari.ButtonStyle.SECONDARY, custom_id='rock')
    async def rock(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        player = self.players.get(ctx.user.id)

        if player.choice is None:
            player.choose('rock')
            await self.update(ctx)
        else:
            embed = hikari.Embed(description='You have already made a choice!', color=get_setting('general', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    
    @miru.button(label='Paper', emoji='🗞️', style=hikari.ButtonStyle.SECONDARY, custom_id='paper')
    async def paper(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        player = self.players.get(ctx.user.id)

        if player.choice is None:
            player.choose('paper')
            await self.update(ctx)
        else:
            embed = hikari.Embed(description='You have already made a choice!', color=get_setting('general', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    
    @miru.button(label='Scissors', emoji='✂️', style=hikari.ButtonStyle.SECONDARY, custom_id='scissors')
    async def scissors(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        player = self.players.get(ctx.user.id)

        if player.choice is None:
            player.choose('scissors')
            await self.update(ctx)
        else:
            embed = hikari.Embed(description='You have already made a choice!', color=get_setting('general', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    async def update(self, ctx: miru.ViewContext) -> None:
        player1 = list(self.players.values())[0]
        player2 = list(self.players.values())[1]

        if player1.choice and player2.choice:
            return await self.show_result()
        
        self.embed.set_image(self.display(hidden=True))
        await self.ctx.edit_last_response(self.embed, components=self.build())
    
    async def start_next_round(self) -> None:
        self.rounds += 1

        for player in self.players.values():
            player.reset()
            if isinstance(player, AIPlayer):
                player.choose()

        self.embed.title = f'Round {self.rounds:,}: Rock, Paper, Scissors!'
        self.embed.description = (
            f'Choose your weapon to duel!\n\n'
            f'> **Offering Bet**: {self.bet:,} 🪙\n'
            f'> **Payout Winnings**: {self.bet * 2:,} 🪙'
        )
        self.embed.set_image(self.display(hidden=True))
        self.embed.set_footer(text=f'You have {self.timeout:,.0f} seconds to choose an action!')
        await self.ctx.edit_last_response(self.embed, components=self.build())

    async def show_result(self) -> None:
        winner = self.check_winner()

        if winner:
            winner.wins += 1

            if winner.wins == self.wins:
                loser = list(self.players.values())[0] if list(self.players.values())[0] != winner else list(self.players.values())[1]
                
                if not isinstance(winner, AIPlayer):
                    economy.add_money(winner.user.id, self.bet * 2, False)
                    economy.add_gain(winner.user.id, self.bet)
                if not isinstance(loser, AIPlayer):
                    economy.add_loss(loser.user.id, self.bet)
                
                self.embed.title = f'{winner.user.display_name} wins the rps duel!'
                self.embed.description = (
                    f'<@{winner.user.id}> has won the duel against <@{loser.user.id}>! The bet has been paid out to the winner.\n\n'
                    f'> **Total Rounds**: {self.rounds:,}\n'
                    f'> **Offering Bet**: {self.bet:,} 🪙\n'
                    f'> **Payout Winnings**: {self.bet * 2:,} 🪙'
                )
                self.embed.set_image(self.display(hidden=False, winner=winner))
                self.embed.set_footer(None)
                await self.ctx.edit_last_response(self.embed, components=[])
                
                return self.stop()
                
        self.embed.set_image(self.display())
        self.embed.set_footer(None)
        await self.ctx.edit_last_response(self.embed, components=[])
        
        await asyncio.sleep(3)
        
        await self.start_next_round()

    async def on_timeout(self) -> None:
        player1 = list(self.players.values())[0]
        player2 = list(self.players.values())[1]

        if player1.choice is None and player2.choice is None:
            if not isinstance(player1, AIPlayer):
                economy.add_money(player1.user.id, self.bet, False)
            if not isinstance(player2, AIPlayer):
                economy.add_money(player2.user.id, self.bet, False)
            
            self.embed.title = 'Duel timed out!'
            self.embed.description = (
                f'Both players have failed to make a choice in time! The bet has been refunded.\n\n'
                f'> **Total Rounds**: {self.rounds:,}\n'
                f'> **Offering Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Winnings**: {self.bet * 2:,} 🪙'
            )
            self.embed.set_image(self.display(hidden=True))
            self.embed.set_footer(None)
        elif player1.choice is None:
            if not isinstance(player2, AIPlayer):
                economy.add_money(player2.user.id, self.bet * 2, False)
                economy.add_gain(player2.user.id, self.bet)
            if not isinstance(player1, AIPlayer):
                economy.add_loss(player1.user.id, self.bet)
            
            self.embed.title = 'Duel timed out!'
            self.embed.description = (
                f'<@{player1.user.id}> has failed to make a choice in time! The bet has been paid out to <@{player2.user.id}>.\n\n'
                f'> **Total Rounds**: {self.rounds:,}\n'
                f'> **Offering Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Winnings**: {self.bet * 2:,} 🪙'
            )
            self.embed.set_image(self.display(hidden=True, winner=player2))
            self.embed.set_footer(None)
        else:
            if not isinstance(player1, AIPlayer):
                economy.add_money(player1.user.id, self.bet * 2, False)
                economy.add_gain(player1.user.id, self.bet)
            if not isinstance(player2, AIPlayer):
                economy.add_loss(player2.user.id, self.bet)
            
            self.embed.title = 'Duel timed out!'
            self.embed.description = (
                f'<@{player2.user.id}> has failed to make a choice in time! The bet has been paid out to <@{player1.user.id}>.\n\n'
                f'> **Total Rounds**: {self.rounds:,}\n'
                f'> **Offering Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Winnings**: {self.bet * 2:,} 🪙'
            )
            self.embed.set_image(self.display(hidden=True, winner=player1))
            self.embed.set_footer(None)

        await self.ctx.edit_last_response(self.embed, components=[]) 
        return self.stop()

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id in self.players

    def check_winner(self) -> Player:
        player1 = list(self.players.values())[0]
        player2 = list(self.players.values())[1]

        if player1.choice == player2.choice:
            return None
        elif player1.choice == 'rock' and player2.choice == 'scissors':
            return player1
        elif player1.choice == 'paper' and player2.choice == 'rock':
            return player1
        elif player1.choice == 'scissors' and player2.choice == 'paper':
            return player1
        else:
            return player2

    def display(self, hidden: bool = False, winner: Player = None) -> bytes:
        player1 = list(self.players.values())[0]
        player2 = list(self.players.values())[1]

        menu = Image.open(MENU_IMAGE_PATH).convert('RGBA')
        thinking = Image.open(THINKING_IMAGE_PATH).convert('RGBA')
        selected = Image.open(SELECTED_IMAGE_PATH).convert('RGBA')
        rock = Image.open(ROCK_IMAGE_PATH).convert('RGBA')
        paper = Image.open(PAPER_IMAGE_PATH).convert('RGBA')
        scissors = Image.open(SCISSORS_IMAGE_PATH).convert('RGBA')
        choices = {'rock': rock, 'paper': paper, 'scissors': scissors}
        
        if hidden:
            menu.paste(thinking, (132, 136), thinking) if player1.choice is None else menu.paste(selected, (132, 136), selected)
            menu.paste(thinking, (528, 136), thinking) if player2.choice is None else menu.paste(selected, (528, 136), selected)
        else:
            menu.paste(choices.get(player1.choice).transpose(Image.FLIP_LEFT_RIGHT), (132, 136), choices.get(player1.choice).transpose(Image.FLIP_LEFT_RIGHT))
            menu.paste(choices.get(player2.choice), (528, 136), choices.get(player2.choice))

        draw = ImageDraw.Draw(menu)
        font = ImageFont.truetype('assets/font/ThaleahFat.ttf', size=64)
        draw.text((204, 32), player1.user.display_name, font=font, fill=(255, 255, 255), anchor='mm', align='center')
        draw.text((604, 32), player2.user.display_name, font=font, fill=(255, 255, 255), anchor='mm', align='center')
        draw.text((204, 80), f'{player1.wins:,}', font=font, fill=(255, 255, 255), anchor='mm', align='center')
        draw.text((604, 80), f'{player2.wins:,}', font=font, fill=(255, 255, 255), anchor='mm', align='center')
        draw.text((400, 360), f'First one to {self.wins} wins!', font=font, fill=(255, 255, 255), anchor='mm', align='center')

        if winner:
            winnerAvatar = Image.open(BytesIO(requests.get(winner.user.avatar_url).content)).convert('RGBA') if winner.user.avatar_url else Image.open(BytesIO(requests.get(winner.user.default_avatar_url).content)).convert('RGBA')
            win = Image.open(WIN_IMAGE_PATH).convert('RGBA')
            winnerAvatar = circle(winnerAvatar, (120, 120))
            
            menu.paste(win, (0, 0), win)
            menu.paste(winnerAvatar, (340, 164), winnerAvatar)

            draw.text((400, 120), f'{winner.user.display_name} wins!', font=font, fill=(255, 255, 255), anchor='mm', align='center')

        with BytesIO() as a:
            menu.save(a, 'PNG')
            a.seek(0)
            return a.getvalue()

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('wins', 'How many wins does a player need to win.', type=int, min_value=1, max_value=10, required=True)
@lightbulb.option('bet', 'Number of coins you want to bet.', type=int, min_value=0, max_value=1000, required=True)
@lightbulb.option('user', 'The user to play against.', type=hikari.Member, required=True)
@lightbulb.command('rps', 'Challenge a Discord member to a game of Rock-Paper-Scissors.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def rps(ctx: lightbulb.Context, user: hikari.Member, bet: int, wins: int) -> None:
    if ctx.author.id == user.id:
        embed = hikari.Embed(description='You are not allowed to challenge yourself!', color=get_setting('general', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif not economy.remove_money(ctx.author.id, bet, False):
        embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return

    if user.is_bot:
        bot = AIPlayer(user)
        players = {ctx.author.id: Player(ctx.member), user.id: bot}
        timeout = 60

        embed = hikari.Embed(
            title = 'Round 1: Rock, Paper, Scissors!',
            description = (
                f'Choose your weapon to duel!\n\n'
                f'> **Offering Bet**: {bet:,} 🪙\n'
                f'> **Payout Winnings**: {bet * 2:,} 🪙'
            ),
            color=get_setting('general', 'embed_color')
        )
        embed.set_footer(text=f'You have {timeout:,.0f} seconds to choose an action!')

        view = RPSView(ctx, embed, players, bet, wins, timeout)
        players.get(user.id).choose()
        embed.set_image(view.display(hidden=True))
    else:
        timeout = 300

        embed = hikari.Embed(
            title=f'A wild duel request appeared!', 
            description=f'<@{ctx.author.id}> has challenged <@{user.id}> to a rock, paper, scissors duel!\n\n'
                        f'> **Win Condition**: First to {wins:,} win(s).\n'
                        f'> **Offering Bet**: {bet:,} 🪙\n'
                        f'> **Payout Winnings**: {bet * 2:,} 🪙',
            color=get_setting('general', 'embed_color')
        )
        embed.set_footer(f'The duel request will timeout in {timeout/60:,.0f} minutes!')
        
        view = DuelView(ctx, embed, ctx.member, user, bet, wins, timeout)
        embed.set_image(view.display())

    await ctx.respond(embed, components=view.build())
    ctx.bot.d.get('client').start_view(view)

def load(bot):
    bot.add_plugin(plugin)