import hikari
import lightbulb
import miru
import sqlite3
import random

from lightbulb.ext import tasks
from datetime import datetime
from bot import get_setting, verify_user

plugin = lightbulb.Plugin('Economy')
leaderboardEco = []
leaderboardEcoLastRefresh = None

## Leaderboard Command ##

@tasks.task(m=30, auto_start=True)
async def update_leaderboard():
    global leaderboardEco, leaderboardEcoLastRefresh
    leaderboardEco = []
    leaderboardEcoLastRefresh = datetime.now().astimezone()

    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    query = "SELECT user_id, balance, tpass FROM economy ORDER BY balance DESC"
    cursor.execute(query)
    results = cursor.fetchall()

    rank = 0
    lastBalance = None

    for result in results:
        user_id, balance, tpass = result
        if balance != lastBalance:
            rank += 1
            lastBalance = balance
        
        if rank == 1:
            leaderboardEco.append({'user_id': user_id, 'balance': balance, 'tpass': tpass, 'rank': '🥇'})
        elif rank == 2:
            leaderboardEco.append({'user_id': user_id, 'balance': balance, 'tpass': tpass, 'rank': '🥈'})
        elif rank == 3:
            leaderboardEco.append({'user_id': user_id, 'balance': balance, 'tpass': tpass, 'rank': '🥉'})
        else:
            leaderboardEco.append({'user_id': user_id, 'balance': balance, 'tpass': tpass, 'rank': f'{rank}.'})
    
    db.commit()
    cursor.close()
    db.close()

@plugin.command
@lightbulb.command('leaderboard', 'Displays leaderboard rankings.', aliases=['baltop'], pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def baltop(ctx: lightbulb.SlashContext) -> None:
    rankings = []
    balances = []
    tpasses = []
    
    if len(leaderboardEco) > 0:
        try:
            for i in range(10):
                rankings.append(f'{leaderboardEco[i]["rank"]} <@{leaderboardEco[i]["user_id"]}>')
                balances.append(f'🪙 {leaderboardEco[i]["balance"]:,}')
                tpasses.append(f'🎟️ {leaderboardEco[i]["tpass"]:,}')
        except IndexError:
            pass

        embed = hikari.Embed(title='Economy Leaderboard', color=get_setting('embed_color'), timestamp=leaderboardEcoLastRefresh)
        embed.add_field(name='Discord User', value='\n'.join(rankings), inline=True)
        embed.add_field(name='Balance', value='\n'.join(balances), inline=True)
        embed.add_field(name='Tux Pass', value='\n'.join(tpasses), inline=True)
        embed.set_footer(f'Last updated')
    else:
        embed = hikari.Embed(title='Economy Leaderboard', color=get_setting('embed_color'), timestamp=leaderboardEcoLastRefresh)
        embed.add_field(name='Discord User', value='🥇 Unknown', inline=True)
        embed.add_field(name='Balance', value='🪙 0', inline=True)
        embed.add_field(name='Tux Pass', value='🎟️ 0', inline=True)
        embed.set_footer(f'Last updated')
    
    await ctx.respond(embed)

## Balance Command ##

@plugin.command
@lightbulb.option('user', 'The user to get information about.', type=hikari.User, required=False)
@lightbulb.command('balance', 'Get balance on a server member.', aliases=['bal'], pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def balance(ctx: lightbulb.SlashContext, user: hikari.User) -> None:
    if user == None: # if no user has been sent
        user = ctx.author
    elif user.is_bot: # user has been sent. checks if user is a bot
        embed = hikari.Embed(description="Bots don't have the rights to earn money!", color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    username = user.username
    
    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    
    cursor.execute(f'SELECT balance, total, loss, tpass FROM economy WHERE user_id = {user.id}') # moves cursor to user's balance, total, and tpass from database
    bal = cursor.fetchone() # grabs the values of user's balance and total
    
    try: # just in case for errors
        balance = bal[0] # balance SHOULD be at index 0
        total = bal[1] # total SHOULD be at index 1
        loss = bal[2] # loss SHOULD be at index 2
        tpass = bal[3] # tpass SHOULD be at index 3
    except:
        balance = 0
        total = 0
        loss = 0
        tpass = 0
    
    cursor.close()
    db.close()
    
    embed = (
        hikari.Embed(title=f"{username}'s Balance", description=f'Wallet: 🪙 {balance:,}\nNet Gain: 🪙 {total:,}\nNet Loss: 🪙 {loss:,}\nTux Pass: {tpass:,} 🎟️', color=get_setting('embed_color'), timestamp=datetime.now().astimezone())
        .set_footer(text=f'Requested by {ctx.author.username}', icon=ctx.author.display_avatar_url)
        .set_thumbnail(user.avatar_url if user.avatar_url != None else user.default_avatar_url)
    )
    
    await ctx.respond(embed)

## Daily Command ##

@plugin.command
@lightbulb.add_cooldown(length=86400.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.command('daily', 'Get your daily reward!')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def daily(ctx: lightbulb.Context) -> None:
    user = ctx.author
    earnings = random.randint(120,360)
    
    if verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif add_money(user.id, earnings, True):
        embed = (hikari.Embed(description=f'You earned 🪙 {earnings}!', color=get_setting('embed_color')))
        await ctx.respond(embed)
    
    return

## Pay Command ##

@plugin.command
@lightbulb.option('number', 'The number of coins', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', 'The user you are about to pay.', type=hikari.User, required=True)
@lightbulb.command('pay', 'Give a server member money.', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def pay(ctx: lightbulb.SlashContext, user: hikari.User, number: int) -> None:
    if user.is_bot or ctx.author.id == user.id: # checks if the user is a bot or the sender
        embed = hikari.Embed(description='You are not allowed to send money to this user!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    sender = ctx.author

    if verify_user(sender) == None: # if user has never been register
        embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif remove_money(sender.id, number, False) == False:
        embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    add_money(user.id, number, False)
    
    embed = (hikari.Embed(description=f'You sent 🪙 {number:,} to {user.username}!', color=get_setting('embed_color')))
    await ctx.respond(embed)

## Coinflip Command ##

@plugin.command
@lightbulb.option('number', 'Number of coinflip(s)', type=int, min_value=1, max_value=100, required=True)
@lightbulb.command('coinflip', 'Flips a coin.', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def coinflip(ctx: lightbulb.SlashContext, number: int) -> None:
    result = []
    heads = 0
    tails = 0

    for i in range(number):
        number = random.randint(1,2)
        if number == 1:
            result.append('Heads')
            heads += 1
        else:
            result.append('Tails')
            tails += 1

    result = (', '.join(result))

    embed = (hikari.Embed(title='Coinflip Result(s):', description=result, color=get_setting('embed_color')))
    embed.add_field('Summary:', f'Heads: {heads} Tails: {tails}')
    await ctx.respond(embed)

## Draw Command ##

class DrawButton(miru.Button):
    def __init__(self) -> None:
        super().__init__(style=hikari.ButtonStyle.PRIMARY, label='Draw')
    
    async def callback(self, ctx: miru.Context) -> None:
        self.view.action = 'Draw'
        self.view.stop()

class Draw5Button(miru.Button):
    def __init__(self) -> None:
        super().__init__(style=hikari.ButtonStyle.SUCCESS, label='Draw 5')
    
    async def callback(self, ctx: miru.Context) -> None:
        self.view.action = 'Draw 5'
        self.view.stop()

class CheckView(miru.View):
    def __init__(self, author: hikari.User) -> None:
        self.author = author
        super().__init__(timeout=60.0)
        
    async def view_check(self, ctx: miru.Context) -> bool:
        return ctx.user.id == self.author.id

@plugin.command
@lightbulb.command('draw', 'Draw cards from a deck.')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def draw(ctx: lightbulb.Context):
    player = ctx.author
    deck = [
        '1 ♥️', '1 ♠️', '1 ♣️', '1 ♦️', 
        '2 ♥️', '2 ♠️', '2 ♣️', '2 ♦️', 
        '3 ♥️', '3 ♠️', '3 ♣️', '3 ♦️', 
        '4 ♥️', '4 ♠️', '4 ♣️', '4 ♦️', 
        '5 ♥️', '5 ♠️', '5 ♣️', '5 ♦️',
        '6 ♥️', '6 ♠️', '6 ♣️', '6 ♦️',
        '7 ♥️', '7 ♠️', '7 ♣️', '7 ♦️',
        '8 ♥️', '8 ♠️', '8 ♣️', '8 ♦️',
        '9 ♥️', '9 ♠️', '9 ♣️', '9 ♦️',
        '10 ♥️', '10 ♠️', '10 ♣️', '10 ♦️',
        'J ♥️', 'J ♠️', 'J ♣️', 'J ♦️',
        'Q ♥️', 'Q ♠️', 'Q ♣️', 'Q ♦️',
        'K ♥️', 'K ♠️', 'K ♣️', 'K ♦️'
    ]
    
    view = CheckView(player)
    view.add_item(DrawButton())
    view.add_item(Draw5Button())
    
    card = get_card(deck)
    deck.remove(card)

    embed = hikari.Embed(title=f'Cards Remaining: {len(deck)}', description=f"Your card: {get_card_str(card)}", color=get_setting('embed_color'))
    message = await ctx.respond(embed,components=view.build())
    message = await message
    
    await view.start(message)
    await view.wait()

    while True:
        if hasattr(view, 'action'):
            match view.action:
                case 'Draw':
                    if len(deck) >= 1:
                        card = get_card(deck)
                        deck.remove(card)
                        embed = hikari.Embed(title=f'Cards Remaining: {len(deck)}', description=f"Your card: {get_card_str(card)}", color=get_setting('embed_color'))
                    else:
                        return await ctx.edit_last_response(hikari.Embed(description=f"There are no more cards in this deck.", color=get_setting('embed_color')))
                case 'Draw 5':
                    if len(deck) >= 5:
                        cards = []
                        for i in range(5):
                            card = get_card(deck)
                            cards.append(get_card_str(card))
                            deck.remove(card)
                        embed = hikari.Embed(title=f'Cards Remaining: {len(deck)}', description=f"Your cards: {', '.join(cards)}", color=get_setting('embed_color'))
                    elif len(deck) < 5 and len(deck) > 0:
                        cards = []
                        for i in range(len(deck)):
                            card = get_card(deck)
                            cards.append(get_card_str(card))
                            deck.remove(card)
                        embed = hikari.Embed(title=f'Cards Remaining: {len(deck)}', description=f"Your cards: {', '.join(cards)}", color=get_setting('embed_color'))
                    else:
                        return await ctx.edit_last_response(hikari.Embed(description=f"There are no more cards in this deck.", color=get_setting('embed_color')))
        else:
            embed = hikari.Embed(description=f"Menu has closed due to inactivity.", color=get_setting('embed_color'))
            await ctx.edit_last_response(embed, components=[])
            return
        
        view = CheckView(player)
        view.add_item(DrawButton())
        view.add_item(Draw5Button())
        message = await ctx.edit_last_response(embed, components=view.build())
        await view.start(message)
        await view.wait()

## Russian Roulette ##

@plugin.command
@lightbulb.option('bet', 'The amount players will bet.', type=int, min_value=100, max_value=None, required=True)
@lightbulb.option('capacity', 'How many bullet?', type=int, min_value=6, max_value=100, required=True)
@lightbulb.command('russian-roulette', 'Play a game of Russian Roulette.', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def russian_roulette(ctx: lightbulb.Context, capacity: int, bet: int):
    if verify_user(ctx.user) == None: # if user has never been register
        embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif remove_money(ctx.user.id, bet, False) == False: # if user has enough money
        embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return

    players = {f'<@{ctx.user.id}>': {'name': f'{ctx.user.username}', 'id': ctx.user.id, 'url': ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url}}
    
    embed = hikari.Embed(title=f'{ctx.user.username} has started a Russian Roulette game!', description='`DO NOT WORRY! YOU WILL NOT DIE IN REAL LIFE!\nYOU WILL ONLY HURT YOUR SELF ESTEEM!`', color=get_setting('embed_color'))
    embed.set_image('assets/img/revolver.png')
    embed.add_field(name='__Game info__', value=f'Initial Bet: 🪙 {bet:,}\nBet Pool: 🪙 {bet:,}\nChamber Capacity: `{capacity:,}`', inline=True)
    embed.add_field(name='__Player List__', value=f'{", ".join(players)}', inline=True)
    embed.set_footer(text=f'The game will timeout in 2 minutes!')
    
    view = RRLobbyView(ctx.author, players, capacity, bet)
    
    message = await ctx.respond(embed, components=view.build())
    message = await message
    
    await view.start(message) # starts up lobby
    await view.wait() # waiting until lobby starts or timed out
    
    if not view.gameStart: # if lobby timed out
        return
    
    embed = hikari.Embed(title=f"It's {ctx.user.username} Turn!", description=f'Players: {", ".join(view.game["players"])}\nBet Pool: 🪙 {view.game["pool"]:,}\nBullets Remaining: `{view.game["capacity"]}`', color=get_setting('embed_color'))
    embed.set_image('assets/img/revolver.png')
    embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
    embed.set_footer(text=f'You have {15.0} seconds to choose an action!')
        
    view = RRGameView(view.game, 15.0)
        
    message = await ctx.edit_last_response(embed, components=view.build())

    await view.start(message) # starts game
    
class RRLobbyView(miru.View):
    def __init__(self, author: hikari.User, players: dict, capacity: int, amount: int) -> None:
        super().__init__(timeout=120.0)
        self.game = {'author': author, 'players': players, 'capacity': capacity, 'amount': amount, 'pool': amount}
        self.gameStart = False
    
    @miru.button(label='Start', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def start_game(self, button: miru.Button, ctx: miru.Context) -> None:
        if self.game.get('author').id != ctx.user.id: # checks if user is host
            embed = hikari.Embed(description='You are not the host!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif len(self.game['players']) == 1:
            embed = hikari.Embed(description='You do not have enough players!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif self.game['pool'] % (len(self.game['players']) - 1) != 0:
            embed = hikari.Embed(description="Loser's bet cannot be distributed equally with the current amount of players!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        self.gameStart = True
        self.stop()
    
    @miru.button(label='Join Game', style=hikari.ButtonStyle.PRIMARY, row=1)
    async def join(self, button: miru.Button, ctx: miru.Context) -> None:
        player = f'<@{ctx.user.id}>'
        playerInfo = {'name': f'{ctx.user.username}', 'id': ctx.user.id, 'url': ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url}
        
        if player in self.game['players']: # checks if user already joined
            embed = hikari.Embed(description='You already joined this game!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif verify_user(ctx.user) == None: # if user has never been register
            embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif remove_money(ctx.user.id, self.game['amount'], False) == False: # if user has enough money
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return

        self.game['players'][player] = playerInfo
        self.game['pool'] = self.game['pool'] + self.game['amount']
        
        embed = hikari.Embed(title=f'{self.game["author"]} has started a Russian Roulette game!', description='`DO NOT WORRY! YOU WILL NOT DIE IN REAL LIFE!\nYOU WILL ONLY HURT YOUR SELF ESTEEM!`', color=get_setting('embed_color'))
        embed.set_image('assets/img/revolver.png')
        embed.add_field(name='__Game info__', value=f"Initial Bet: 🪙 {self.game['amount']:,}\nBet Pool: 🪙 {self.game['pool']:,}\nChamber Capacity: `{self.game['capacity']:,}`", inline=True)
        embed.add_field(name='__Player List__', value=f'{", ".join(self.game["players"])}', inline=True)
        embed.set_footer(text=f'The game will timeout in 2 minutes!')
        
        await ctx.message.edit(embed)
        
    @miru.button(label='Refund', style=hikari.ButtonStyle.DANGER, row=1)
    async def refund(self, button: miru.Button, ctx: miru.Context) -> None:
        if self.game['author'].id != ctx.user.id: # checks if user is host
            embed = hikari.Embed(description='You are not the host!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        for player in self.game['players'].values():
            add_money(player['id'], self.game['amount'], False)
        
        embed = hikari.Embed(title=f"{self.game.get('author')} has refunded all bets!", description='`DO NOT WORRY! YOU WILL NOT DIE IN REAL LIFE!\nYOU WILL ONLY HURT YOUR SELF ESTEEM!`', color=get_setting('embed_color'))
        embed.set_image('assets/img/revolver.png')
        embed.add_field(name='__Game info__', value=f"Initial Bet: 🪙 {self.game['amount']:,}\nBet Pool: 🪙 {self.game['pool']:,}\nChamber Capacity: `{self.game['capacity']:,}`", inline=True)
        embed.add_field(name='__Player List__', value=f'{", ".join(self.game["players"])}', inline=True)
        
        await ctx.edit_response(embed, components=[])
    
    async def on_timeout(self) -> None:
        for player in self.game['players'].values():
            add_money(player['id'], self.game['amount'], False)
        
        embed = hikari.Embed(title=f"Game has timed out! All bets have been refunded!", color=get_setting('embed_color'))
        embed.set_image('assets/img/revolver.png')
        embed.add_field(name='__Game info__', value=f"Initial Bet: 🪙 {self.game['amount']:,}\nBet Pool: 🪙 {self.game['pool']:,}\nChamber Capacity: `{self.game['capacity']:,}`", inline=True)
        embed.add_field(name='__Player List__', value=f'`{", ".join(self.game["players"])}`', inline=True)
        
        await self.message.edit(embed, components=[])
    
    async def view_check(self, ctx: miru.Context) -> bool:
        return True

class RRGameView(miru.View):
    def __init__(self, game: dict, timeout: float) -> None:
        super().__init__(timeout=timeout)
        self.game = game
        self.playerIter = iter(game['players'].items())
        self.player = next(self.playerIter)[1]
        self.chamber = [True]
        self.gameMessages = ['Huh, there seems to be no bullet...', 'You got lucky this time!', "Beginner's luck!", 'You should end turn before it gets dangerous!', 'Sigh... No bullet this time.', 'You are safe, for now...', 'You lost! Just kidding, but it was close!', 'Nice flinch!']
        self.endTurn = False
        
        for i in range(self.game['capacity'] - 1):
            self.chamber.append(False)
        
        random.shuffle(self.chamber)
    
    @miru.button(label='Fire', emoji='💥', style=hikari.ButtonStyle.PRIMARY, row=1)
    async def fire(self, button: miru.Button, ctx: miru.Context):
        if len(self.chamber) == 0:
            return
        elif self.chamber[0]:
            embed = hikari.Embed(title=f"Oh no! {self.player['name']} shot themself!", description=f'`{self.player["name"]} bet has been distributed among the winners!`\n\nPlayers: {", ".join(self.game["players"])}\nBet Pool: 🪙 {self.game["pool"]:,}\nBullets Remaining: `{len(self.chamber) - 1}`', color=get_setting('embed_color'))
            embed.set_image('assets/img/revolver.png')
            embed.set_thumbnail(self.player['url'])
            
            for player in self.game['players'].values(): 
                if player['id'] != self.player['id']: # check if player is not the loser
                    add_money(player['id'], self.game['pool'] / (len(self.game['players']) - 1), False)
                    add_gain(player['id'], self.game['amount'])
            add_loss(self.player['id'], self.game['amount'])
            
            await ctx.edit_response(embed, components=[])
            self.stop()
            return
        
        self.chamber.pop(0) # removes bullet
        
        embed = hikari.Embed(title=f"It's {self.player['name']} Turn!", description=f'`{self.gameMessages[random.randint(0, len(self.gameMessages) - 1)]}`\n\nPlayers: {", ".join(self.game["players"])}\nBet Pool: 🪙 {self.game["pool"]:,}\nBullets Remaining: `{len(self.chamber)}`', color=get_setting('embed_color'))
        embed.set_image('assets/img/revolver.png')
        embed.set_thumbnail(self.player['url'])
        embed.set_footer(text=f'You have {self.timeout} seconds to choose an action!')
        
        self.endTurn = True
        await ctx.edit_response(embed, components=self.build())
    
    @miru.button(label='End Turn', style=hikari.ButtonStyle.SUCCESS, row=1, disabled=False)
    async def next_turn(self, button: miru.Button, ctx: miru.Context):
        if self.endTurn:
            try: # cycle turns
                self.player = next(self.playerIter)[1]
            except:
                self.playerIter = iter(self.game['players'].items())
                self.player = next(self.playerIter)[1]
        else:
            embed = hikari.Embed(description='You need to fire at least one shot!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        embed = hikari.Embed(title=f"It's {self.player['name']} Turn!", description=f'Players: {", ".join(self.game["players"])}\nBet Pool: 🪙 {self.game["pool"]:,}\nBullets Remaining: `{len(self.chamber)}`', color=get_setting('embed_color'))
        embed.set_image('assets/img/revolver.png')
        embed.set_thumbnail(self.player['url'])
        embed.set_footer(text=f'You have {self.timeout} seconds to choose an action!')
        
        self.endTurn = False
        await ctx.edit_response(embed, components=self.build())
    
    async def on_timeout(self) -> None:
        embed = hikari.Embed(title=f"Oh no! {self.player['name']} took too long and the gun exploded!", description=f'`{self.player["name"]} bet has been distributed among the winners!`\n\nPlayers: {", ".join(self.game["players"])}\nBet Pool: 🪙 {self.game["pool"]:,}\nBullets Remaining: `{len(self.chamber) - 1}`', color=get_setting('embed_color'))
        embed.set_image('assets/img/revolver.png')
        embed.set_thumbnail(self.player['url'])
        
        for player in self.game['players'].values(): 
            if player['id'] != self.player['id']: # check if player is not the loser
                add_money(player['id'], self.game['pool'] / (len(self.game['players']) - 1), False)
                add_gain(player['id'], self.game['amount'])
        add_loss(self.player['id'], self.game['amount'])
            
        await self.message.edit(embed, components=[])
    
    async def view_check(self, ctx: miru.Context) -> bool:
        return ctx.user.id == self.player['id']

## RPS Command ##

@plugin.command
@lightbulb.option('wins', 'How many wins does a player need to win.', type=int, min_value=1, max_value=10, required=True)
@lightbulb.option('bet', 'Number of coins you want to bet.', type=int, min_value=0, max_value=2000, required=True)
@lightbulb.option('user', 'The user to play against.', hikari.User, required=True)
@lightbulb.command('rps', 'Play a game of RPS against a server member.', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def rps(ctx: lightbulb.Context, user: hikari.User, bet: int, wins: int) -> None:
    if user.is_bot or ctx.author.id == user.id: # checks if the user is a bot or the sender
        embed = hikari.Embed(description='You are not allowed to challenge this user!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif remove_money(ctx.author.id, bet, False) == False:
        embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    embed = hikari.Embed(
        title=f'A wild duel request appeared!',
        description=f'**{ctx.author}** has challenged **{user}** to a RPS duel!',
        color=get_setting('embed_color')
    )
    embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
    embed.add_field(name='__Game Info__', value=f'Win Condition: First to `{wins}`!\nBet: 🪙 {bet}')
    embed.set_footer('The duel request will timeout in 2 minutes!')
    
    view = DuelView(ctx.author, user, bet, wins)
    
    message = await ctx.respond(embed, components=view.build())
    
    await view.start(message)
    await view.wait()
    
    if not view.accepted:
        return
    
    embed = hikari.Embed(
        title=f"It's Time to D-D-D-D-D-D DUEL!",
        description=f'Winner will receive 🪙 {bet*2}!',
        color=get_setting('embed_color')
    )
    embed.set_thumbnail('assets/img/revolver.png')
    embed.add_field(name=f'{ctx.author} [0]', value='❔', inline=False)
    embed.add_field(name=f'{user} [0]', value='❔', inline=False)
    embed.set_footer('You have 60 seconds to choose an action or you will automatically forfeit!')
    
    view = RPSGameView(embed, ctx.author, user, bet, wins)
    
    message = await ctx.edit_last_response(embed, components=view.build())
    
    await view.start(message)
    await view.wait()
    
    if view.player1['score'] > view.player2['score']:
        add_loss(user.id, bet)
        add_money(ctx.author.id, bet*2, True)
        
        embed.title = f'{ctx.author} wins the RPS duel!'
        embed.description = f'🪙 {bet*2} coins has been sent to the winner!'
        embed.set_footer(text='')
        
        await ctx.edit_last_response(embed, components=[])
    elif view.player1['score'] < view.player2['score']:
        add_loss(ctx.author.id, bet)
        add_money(user.id, bet*2, True)
        
        embed.title = f'{user} wins the RPS duel!'
        embed.description = f'🪙 {bet*2} coins has been sent to the winner!'
        embed.set_footer(text='')
        
        await ctx.edit_last_response(embed, components=[])
    else:
        add_money(ctx.author.id, bet, False)
        add_money(user.id, bet, False)
        
        embed.title = f'The RPS duel ends in a tie!'
        embed.description = f'Both players were refunded!'
        embed.set_footer(text='')
        
        await ctx.edit_last_response(embed, components=[])
    
class DuelView(miru.View):
    def __init__(self, author: hikari.User, opponent: hikari.User, bet: int, wins: int) -> None:
        super().__init__(timeout=120.0, autodefer=True)
        self.author = author
        self.opponent = opponent
        self.bet = bet
        self.wins = wins
        self.accepted = False

    @miru.button(label='Accept', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def accept(self, button: miru.Button, ctx: miru.Context) -> None:
        if remove_money(self.opponent.id, self.bet, False) == False:
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
    
        self.accepted = True
        self.stop()
    
    @miru.button(label='Decline', style=hikari.ButtonStyle.DANGER, row=1)
    async def decline(self, button: miru.Button, ctx: miru.Context) -> None:
        add_money(self.author.id, self.bet, False)
        
        embed = hikari.Embed(
            title=f'{self.opponent} has declined the duel request!',
            description=f'**{self.author}** has challenged **{self.opponent}** to a RPS duel!',
            color=get_setting('embed_color')
        )
        embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
        embed.add_field(name='__Game Info__', value=f'Win Condition: First to `{self.wins}`!\nBet: 🪙 {self.bet}')
        
        
        await self.message.edit(embed, components=[])
        self.stop()
    
    async def on_timeout(self) -> None:
        add_money(self.author.id, self.bet, False)
        
        embed = hikari.Embed(
            title=f'The duel request timed out!',
            description=f'**{self.author}** has challenged **{self.opponent}** to a RPS duel!',
            color=get_setting('embed_color')
        )
        embed.set_thumbnail(self.author.avatar_url)
        embed.add_field(name='__Game Info__', value=f'Win Condition: Best of One!\nBet: 🪙 {self.bet}')
        
        await self.message.edit(embed, components=[])
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.opponent.id

class RPSGameView(miru.View):
    def __init__(self, embed: hikari.Embed, author: hikari.User, opponent: hikari.User, bet: int, wins: int) -> None:
        super().__init__(timeout=60.0, autodefer=True)
        self.embed = embed
        self.author = author
        self.opponent = opponent
        self.bet = bet
        self.wins = wins
        self.turn = 1
        
        self.player1 = {'ready': False, 'score': 0, 'actions': []}
        self.player2 = {'ready': False, 'score': 0, 'actions': []}
    
    @miru.button(label='Rock', emoji='🪨', style=hikari.ButtonStyle.SECONDARY, row=1)
    async def rock(self, button: miru.Button, ctx: miru.Context) -> None:
        if ctx.user.id == self.author.id:
            if not self.player1['ready']:
                self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}] ☑️', '❔' if len(self.player1['actions']) < 1 else ' | '.join(self.player1['actions']))
                await ctx.edit_response(self.embed)
                
                self.player1['ready'] = True
                self.player1['actions'].append('🪨')
            else:
                embed = hikari.Embed(description='You already chose an action!', color=get_setting('embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
        elif ctx.user.id == self.opponent.id:
            if not self.player2['ready']:
                self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}] ☑️', '❔' if len(self.player2['actions']) < 1 else ' | '.join(self.player2['actions']))
                await ctx.edit_response(self.embed)
                
                self.player2['ready'] = True
                self.player2['actions'].append('🪨')
            else:
                embed = hikari.Embed(description='You already chose an action!', color=get_setting('embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
        
        # Once everyone chose an action #
        
        if self.player1['ready'] and self.player2['ready']:
            match rps_get_result(self.player1['actions'], self.player2['actions'], self.turn):
                case 'Player1':
                    self.player1['score'] = self.player1['score'] + 1
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ✅'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ❌'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))
                case 'Player2':
                    self.player2['score'] = self.player2['score'] + 1
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ❌'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ✅'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))       
                case 'Tie':
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ✏️'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ✏️'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))

            if self.player1['score'] == self.wins or self.player2['score'] == self.wins:       
                self.stop()
                return
            
            self.player1['ready'] = False
            self.player2['ready'] = False
            
            self.turn = self.turn + 1
            
            await ctx.edit_response(self.embed)

    @miru.button(label='Paper', emoji='📄', style=hikari.ButtonStyle.SECONDARY, row=1)
    async def paper(self, button: miru.Button, ctx: miru.Context) -> None:
        if ctx.user.id == self.author.id:
            if not self.player1['ready']:
                self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}] ☑️', '❔' if len(self.player1['actions']) < 1 else ' | '.join(self.player1['actions']))
                await ctx.edit_response(self.embed)
                
                self.player1['ready'] = True
                self.player1['actions'].append('📄')
            else:
                embed = hikari.Embed(description='You already chose an action!', color=get_setting('embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
        elif ctx.user.id == self.opponent.id:
            if not self.player2['ready']:
                self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}] ☑️', '❔' if len(self.player2['actions']) < 1 else ' | '.join(self.player2['actions']))
                await ctx.edit_response(self.embed)
                
                self.player2['ready'] = True
                self.player2['actions'].append('📄')
            else:
                embed = hikari.Embed(description='You already chose an action!', color=get_setting('embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
        
        # Once everyone chose an action #
        
        if self.player1['ready'] and self.player2['ready']:
            match rps_get_result(self.player1['actions'], self.player2['actions'], self.turn):
                case 'Player1':
                    self.player1['score'] = self.player1['score'] + 1
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ✅'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ❌'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))
                case 'Player2':
                    self.player2['score'] = self.player2['score'] + 1
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ❌'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ✅'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))       
                case 'Tie':
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ✏️'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ✏️'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))

            if self.player1['score'] == self.wins or self.player2['score'] == self.wins:
                self.stop()
                return
            
            self.player1['ready'] = False
            self.player2['ready'] = False
            
            self.turn = self.turn + 1
            
            await ctx.edit_response(self.embed)
        
    @miru.button(label='Scissors', emoji='✂️', style=hikari.ButtonStyle.SECONDARY, row=1)
    async def scissors(self, button: miru.Button, ctx: miru.Context) -> None:
        if ctx.user.id == self.author.id:
            if not self.player1['ready']:
                self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}] ☑️', '❔' if len(self.player1['actions']) < 1 else ' | '.join(self.player1['actions']))
                await ctx.edit_response(self.embed)
                
                self.player1['ready'] = True
                self.player1['actions'].append('✂️')
            else:
                embed = hikari.Embed(description='You already chose an action!', color=get_setting('embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
        elif ctx.user.id == self.opponent.id:
            if not self.player2['ready']:
                self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}] ☑️', '❔' if len(self.player2['actions']) < 1 else ' | '.join(self.player2['actions']))
                await ctx.edit_response(self.embed)
                
                self.player2['ready'] = True
                self.player2['actions'].append('✂️')
            else:
                embed = hikari.Embed(description='You already chose an action!', color=get_setting('embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
        
        # Once everyone chose an action #
        
        if self.player1['ready'] and self.player2['ready']:
            match rps_get_result(self.player1['actions'], self.player2['actions'], self.turn):
                case 'Player1':
                    self.player1['score'] = self.player1['score'] + 1
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ✅'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ❌'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))
                case 'Player2':
                    self.player2['score'] = self.player2['score'] + 1
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ❌'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ✅'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))       
                case 'Tie':
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ✏️'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ✏️'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))

            if self.player1['score'] == self.wins or self.player2['score'] == self.wins:
                self.stop()
                return
            
            self.player1['ready'] = False
            self.player2['ready'] = False
            
            self.turn = self.turn + 1
            
            await ctx.edit_response(self.embed)
    
    async def on_timeout(self) -> None:
        if not self.player1['ready'] and not self.player2['ready']:
            self.stop()
        elif not self.player1['ready']:
            self.player2['score'] = self.wins
            self.stop()
        else:
            self.player1['score'] = self.wins
            self.stop()
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.opponent.id or self.author.id

def rps_get_result(player1Actions: list, player2Actions: list, turn: int) -> str:
    if player1Actions[turn-1] == player2Actions[turn-1]:
        return 'Tie'
    elif player1Actions[turn-1] == '🪨' and player2Actions[turn-1] == '✂️':
        return 'Player1'
    elif player1Actions[turn-1] == '📄' and player2Actions[turn-1] == '🪨':
        return 'Player1'
    elif player1Actions[turn-1] == '✂️' and player2Actions[turn-1] == '📄':
        return 'Player1'
    else:
        return 'Player2'

## Connect 4 Command ##

class Connect4:
    def __init__(self):
        self.board = []
        for i in range(6):
            self.board.append(['🔵'] * 7)
        self.currentPlayer = '1'
  
    def printBoard(self):
        embed = hikari.Embed(description='')
        for row in self.board:
            embed.description = f'{embed.description}\n{" ".join(row)}'
        return embed.description
  
    def makeMove(self, col):
        for i in range(5, -1, -1):
            if self.board[i][col] == '🔵':
                if self.currentPlayer == '1':
                    self.board[i][col] = '🔴'
                else:
                    self.board[i][col] = '🟡'
                return
  
    def hasWon(self, player):
        # check rows
        for row in self.board:
            for i in range(4):
                if row[i:i + 4] == [player] * 4:
                    return True
        # check columns
        for col in range(7):
            for i in range(3):
                if (
                    self.board[i][col] == player
                    and self.board[i + 1][col] == player
                    and self.board[i + 2][col] == player
                    and self.board[i + 3][col] == player
                ):
                    return True
        # check diagonals
        for row in range(3):
            for col in range(4):
                if (
                    self.board[row][col] == player
                    and self.board[row + 1][col + 1] == player
                    and self.board[row + 2][col + 2] == player
                    and self.board[row + 3][col + 3] == player
                ):
                    return True
                if (
                    self.board[row][6 - col] == player
                    and self.board[row + 1][5 - col] == player
                    and self.board[row + 2][4 - col] == player
                    and self.board[row + 3][3 - col] == player
                ):
                    return True
        return False

class Connect4DuelView(miru.View):
    def __init__(self, author: hikari.User, opponent: hikari.User, bet: int) -> None:
        super().__init__(timeout=120.0)
        self.author = author
        self.opponent = opponent
        self.bet = bet
        self.accepted = False
    
    @miru.button(label='Accept', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def accept(self, button: miru.Button, ctx: miru.Context) -> None:
        if remove_money(self.opponent.id, self.bet, False) == False:
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
    
        self.accepted = True
        self.stop()
    
    @miru.button(label='Decline', style=hikari.ButtonStyle.DANGER, row=1)
    async def decline(self, button: miru.Button, ctx: miru.Context) -> None:
        add_money(self.author.id, self.bet, False)
        
        embed = hikari.Embed(
            title=f'{self.opponent} has declined the duel request!',
            description=f'**{self.author}** has challenged **{self.opponent}** to a Connect 4 game!',
            color=get_setting('embed_color')
        )
        embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
        embed.add_field(name='__Game Info__', value=f'Win Condition: Bet: 🪙 {self.bet}')
        
        
        await self.message.edit(embed, components=[])
        self.stop()
    
    async def on_timeout(self) -> None:
        add_money(self.author.id, self.bet, False)
        
        embed = hikari.Embed(
            title=f'The game request timed out!',
            description=f'**{self.author}** has challenged **{self.opponent}** to a Connect 4 game!',
            color=get_setting('embed_color')
        )
        embed.set_thumbnail(self.author.avatar_url)
        embed.add_field(name='__Game Info__', value=f'Bet: 🪙 {self.bet}')
        
        await self.message.edit(embed, components=[])
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.opponent.id

class Connect4GameView(miru.View):
    def __init__(self, game: Connect4, embed: hikari.Embed, author: hikari.User, opponent: hikari.User, bet: int) -> None:
        super().__init__(timeout=None)
        self.game = game
        self.embed = embed
        self.author = author
        self.opponent = opponent
        self.bet = bet
    
    @miru.text_select(
        custom_id='column_select',
        placeholder='Select a Column',
        options=[
            miru.SelectOption(label='1', value='1'),
            miru.SelectOption(label='2', value='2'),
            miru.SelectOption(label='3', value='3'),
            miru.SelectOption(label='4', value='4'),
            miru.SelectOption(label='5', value='5'),
            miru.SelectOption(label='6', value='6'),
            miru.SelectOption(label='7', value='7'),
        ],
        row=1
    )
    async def select_column(self, select: miru.TextSelect, ctx: miru.Context) -> None:
        move = int(select.values[0]) - 1
        player = '🔴' if self.game.currentPlayer == '1' else '🟡'
        
        if move < 0 or move > 6 or self.game.board[0][move] != '🔵':
            await ctx.respond(hikari.Embed(description='Invalid move, try again.', color=get_setting('embed_error_color')), flags=hikari.MessageFlag.EPHEMERAL)
            move = int(select.values[0]) - 1
            return
        self.game.makeMove(move)
        
        if self.game.hasWon(player):
            if self.game.currentPlayer == '1':
                self.embed.description = f'**{self.author.username}** wins!\n{self.game.printBoard()}'
                self.embed.set_thumbnail(self.author.avatar_url if self.author.avatar_url != None else self.author.default_avatar_url)
                add_money(self.author.id, self.bet*2, True)
                add_loss(self.opponent.id, self.bet)
            else:
                self.embed.description = f'**{self.opponent.username}** wins!\n{self.game.printBoard()}'
                self.embed.set_thumbnail(self.opponent.avatar_url if self.opponent.avatar_url != None else self.opponent.default_avatar_url)
                add_money(self.opponent.id, self.bet*2, True)
                add_loss(self.author.id, self.bet)
            self.embed.set_footer(None)
            await ctx.edit_response(self.embed, components=[])
            self.stop()
            return
        
        if self.game.currentPlayer == '1':
            self.game.currentPlayer = '2'
            self.embed.description = f"It's **{self.opponent.username}** turn! Make your move!\n{self.game.printBoard()}"
            self.embed.set_thumbnail(self.opponent.avatar_url if self.opponent.avatar_url != None else ctx.user.default_avatar_url)
        else:
            self.game.currentPlayer = '1'
            self.embed.description = f"It's **{self.author.username}** turn! Make your move!\n{self.game.printBoard()}"
            self.embed.set_thumbnail(self.author.avatar_url if self.author.avatar_url != None else ctx.user.default_avatar_url)
        
        await ctx.edit_response(self.embed)

    async def on_timeout(self) -> None:
        if self.game.currentPlayer == '1':
            self.embed.description = f'**{self.author.username}** wins!\n{self.game.printBoard()}'
            self.embed.set_thumbnail(self.author.avatar_url if self.author.avatar_url != None else self.author.default_avatar_url)
            add_money(self.author.id, self.bet*2, True)
            add_loss(self.opponent.id, self.bet)
        else:
            self.embed.description = f'**{self.opponent.username}** wins!\n{self.game.printBoard()}'
            self.embed.set_thumbnail(self.opponent.avatar_url if self.opponent.avatar_url != None else self.opponent.default_avatar_url)
            add_money(self.opponent.id, self.bet*2, True)
            add_loss(self.author.id, self.bet)
        self.embed.set_footer(None)
        await self.message.edit(self.embed, components=[])
        self.stop()
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        if self.game.currentPlayer == '1':
            return ctx.user.id == self.author.id
        else:
            return ctx.user.id == self.opponent.id

@plugin.command
@lightbulb.option('bet', 'Number of coins you want to bet.', type=int, min_value=0, max_value=2000, required=True)
@lightbulb.option('user', 'The user to play against.', hikari.User, required=True)
@lightbulb.command('connect4', 'Play a game of Connect Four against a server member.', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def connect4(ctx: lightbulb.Context, user: hikari.User, bet: int) -> None:
    if user.is_bot or ctx.author.id == user.id: # checks if the user is a bot or the sender
        embed = hikari.Embed(description='You are not allowed to challenge this user!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif remove_money(ctx.author.id, bet, False) == False:
        embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    embed = hikari.Embed(
        title=f'A wild duel request appeared!',
        description=f'**{ctx.author}** has challenged **{user}** to a Connect Four game!',
        color=get_setting('embed_color')
    )
    embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
    embed.add_field(name='__Game Info__', value=f'Bet: 🪙 {bet}')
    embed.set_footer('The duel request will timeout in 2 minutes!')
    
    view = Connect4DuelView(ctx.author, user, bet)
    
    message = await ctx.respond(embed, components=view.build())
    
    await view.start(message)
    await view.wait()
    
    if not view.accepted:
        return
    
    game = Connect4()
    
    embed = hikari.Embed(title='Welcome to a game of Connect Four!', description=f"It's **{ctx.author.username}** turn! Make your move!\n{game.printBoard()}", color=get_setting('embed_color'))
    embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
    embed.set_footer('You have 60 seconds to choose an option or you will automatically forfeit!')

    view = Connect4GameView(game, embed, ctx.author, user, bet)
    
    message = await ctx.edit_last_response(embed, components=view.build())
    
    await view.start(message)


## BlackJack Command ##

class Deck:
    def __init__(self):
        self.cards = ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K'] * 4
        
    def shuffle(self):
        random.shuffle(self.cards)
        
    def draw(self):
        return self.cards.pop()
    
class Hand:
    def __init__(self, deck):
        self.deck = deck
        self.cards = [deck.draw(), deck.draw()]
        
    def score(self):
        score = 0
        hasAce = False
        for card in self.cards:
            if card in ['J', 'Q', 'K']:
                score += 10
            elif card == 'A':
                score += 1
                hasAce = True
            else:
                score += card
        if hasAce:
            if hasAce and score <= 11:
                score += 10
        return score
    
    def hit(self):
        self.cards.append(self.deck.draw())
        return self.score()
    
    def is_busted(self):
        return self.score() > 21
    
class Player:
    def __init__(self, deck):
        self.hand = Hand(deck)
                
    def is_busted(self):
        return self.hand.is_busted()
    
    def cards(self):
        deck = []
        for card in self.hand.cards:
            deck.append(str(card))
        return deck
        
class Dealer:
    def __init__(self, deck):
        self.hand = Hand(deck)
            
    def is_busted(self):
        return self.hand.is_busted()
    
    def cards(self):
        deck = []
        for c in self.hand.cards:
            deck.append(str(c))
        return deck

class BlackJackView(miru.View):
    def __init__(self, embed: hikari.Embed, author: hikari.User, bet: int, deck: Deck, player: Player, dealer: Dealer) -> None:
        super().__init__(timeout=60.0)
        remove_money(author.id, bet, False)
        self.embed = embed
        self.author = author
        self.bet = bet
        self.deck = deck
        self.player = player
        self.dealer = dealer
    
    @miru.button(label='Hit', style=hikari.ButtonStyle.SUCCESS)
    async def hit(self, button: miru.Button, ctx: miru.Context) -> None:
        self.player.hand.hit()
        
        if self.player.hand.is_busted():
            self.embed.title = 'You Busted!' # Your hand went over 21
            self.embed.description = f"Your hand went over 21 `Bust!`. You lost 🪙 {self.bet}!"
            self.embed.color = get_setting('embed_error_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{", ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{", ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            await ctx.edit_response(self.embed, components=[])
            add_loss(self.author.id, self.bet)
            self.stop()
        elif self.player.hand.score() == 21:
            self.embed.title = 'Blackjack! You have won!' # Your hand value is exactly 21
            self.embed.description = f"Your hand was exactly 21. You won 🪙 {self.bet * 2}!"
            self.embed.color = get_setting('embed_success_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{", ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{", ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            await ctx.edit_response(self.embed, components=[])
            add_money(ctx.author.id, self.bet*2, True)
            self.stop()
        else:
            self.embed.edit_field(0, "Dealer's Hand", f'{self.dealer.cards()[0]}, ?\nValue: ?')
            self.embed.edit_field(1, "Your Hand", f'{", ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            await ctx.edit_response(self.embed)
    
    @miru.button(label='Stand', style=hikari.ButtonStyle.PRIMARY)
    async def stand(self, button: miru.Button, ctx: miru.Context) -> None:
        while self.dealer.hand.score() < 17 or self.dealer.hand.score() < self.player.hand.score():
            self.dealer.hand.hit()
        
        if self.dealer.is_busted():
            self.embed.title = 'Dealer Bust!' # Dealer hand went over 21
            self.embed.description = f"The dealer's hand went over 21, `Bust!`. You won 🪙 {self.bet * 2}!"
            self.embed.color = get_setting('embed_success_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{", ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{", ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            add_money(ctx.author.id, self.bet*2, True)
            self.stop()
        elif self.dealer.hand.score() == 21:
            self.embed.title = 'Blackjack! Dealer has won!' # Dealer hand value is exactly 21
            self.embed.description = f"The dealer's hand was exactly 21. You lost 🪙 {self.bet}!"
            self.embed.color = get_setting('embed_error_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{", ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{", ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            add_loss(self.author.id, self.bet)
            self.stop()
        elif self.player.hand.score() > self.dealer.hand.score():
            self.embed.title = 'You have won!' # Dealer has less value than you
            self.embed.description = f"The dealer's hand had less value in their cards than your hand. You won 🪙 {self.bet * 2}!"
            self.embed.color = get_setting('embed_success_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{", ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{", ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            add_money(ctx.author.id, self.bet*2, True)
            self.stop()
        elif self.player.hand.score() == self.dealer.hand.score():
            self.embed.title = 'Push (Draw)' # Tie
            self.embed.description = f"You and the dealer's hand had the same value of cards."
            self.embed.color = '#FFFF00'
            self.embed.edit_field(0, "Dealer's Hand", f'{", ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{", ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            add_money(ctx.author.id, self.bet, False)
            self.stop()
        else:
            self.embed.title = 'Dealer has won!' # Dealer has more value than you
            self.embed.description = f"The dealer's hand had more value in their cards than your hand. You lost 🪙 {self.bet}!"
            self.embed.color = get_setting('embed_error_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{", ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{", ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            add_loss(self.author.id, self.bet)
            self.stop()

        await ctx.edit_response(self.embed, components=[])
    
    async def on_timeout(self) -> None:
        self.embed.title = 'Dealer has won!' # Game has timed out
        self.embed.description = f"The game has timed out! You lost 🪙 {self.bet}!"
        self.embed.color = get_setting('embed_error_color')
        self.embed.edit_field(0, "Dealer's Hand", f'{", ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
        self.embed.edit_field(1, "Your Hand", f'{", ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
        self.embed.set_footer(None)
        await self.message.edit(self.embed, components=[])
        add_loss(self.author.id, self.bet)
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.author.id

@plugin.command
@lightbulb.option('bet', 'Number of coins you want to bet.', type=int, min_value=20, max_value=2000, required=True)
@lightbulb.command('blackjack', 'Play a game of Blackjack.', aliases=['bj'], pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def blackjack(ctx: lightbulb.Context, bet: int) -> None:
    user = ctx.user
    deck = Deck()
    deck.shuffle()
    player = Player(deck)
    dealer = Dealer(deck)
    
    if player.hand.score() == 21:
        embed = hikari.Embed(title=f'Blackjack! You have won!', description=f'Your hand was exactly 21. You won 🪙 {bet * 2}!', color=get_setting('embed_success_color'))
        embed.add_field(name="Dealer's Hand", value=f'{", ".join(dealer.cards())}\nValue: {dealer.hand.score()}', inline=True)
        embed.add_field(name="Your Hand", value=f'{", ".join(player.cards())}\nValue: {player.hand.score()}', inline=True)
        add_money(ctx.author.id, bet*2, True)
        await ctx.respond(embed)
        return
    elif dealer.hand.score() == 21:
        embed = hikari.Embed(title=f'Blackjack! Dealer has won!', description=f"The dealer's hand was exactly 21. You lost 🪙 {bet}!", color=get_setting('embed_error_color'))
        embed.add_field(name="Dealer's Hand", value=f'{", ".join(dealer.cards())}\nValue: {dealer.hand.score()}', inline=True)
        embed.add_field(name="Your Hand", value=f'{", ".join(player.cards())}\nValue: {player.hand.score()}', inline=True)
        remove_money(ctx.author.id, bet, True)
        await ctx.respond(embed)
        return
    
    embed = hikari.Embed(title=f'BlackJack!', description=f'Choose `Hit` or `Stand`!', color=get_setting('embed_color'))
    embed.add_field(name="Dealer's Hand", value=f'{dealer.cards()[0]}, ?\nValue: ?', inline=True)
    embed.add_field(name="Your Hand", value=f'{", ".join(player.cards())}\nValue: {player.hand.score()}', inline=True)
    embed.set_footer(text='You have 1 minute to choose an action!')
    
    if verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif check_sufficient_amount(user.id, bet) == False:
        embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    view = BlackJackView(embed, user, bet, deck, player, dealer)
    
    message = await ctx.respond(embed, components=view.build())
    await view.start(message)

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

def get_card(cards):
    card = cards[random.randint(0,len(cards)-1)]
    return card

def get_card_str(card):
    string = ''.join(card.split(' '))
    return string

def check_sufficient_amount(userID: str, amount: int) -> bool:
    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    
    cursor.execute(f'SELECT balance FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
    val = cursor.fetchone() # grabs the values of user's balance
    
    try:
        balance = val[0] # balance SHOULD be at index 0
    except:
        balance = 0
        
    cursor.close()
    db.close()
    
    if balance < amount:
        return False

    return True

def set_money(userID: str, amount: int) -> bool:
    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    
    sql = ('UPDATE economy SET balance = ? WHERE user_id = ?')
    val = (amount, userID)
    
    cursor.execute(sql, val) # executes the instructions
    db.commit() # saves changes
    cursor.close()
    db.close()
    
    return True

def add_money(userID: str, amount: int, updateGain: bool) -> bool:
    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    
    cursor.execute(f'SELECT balance, total FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
    val = cursor.fetchone() # grabs the values of user's balance
    
    try:
        balance = val[0] # balance SHOULD be at index 0
        total = val[1] # total SHOULD be at index 1
    except:
        balance = 0
        total = 0
    
    sql = ('UPDATE economy SET balance = ?, total = ? WHERE user_id = ?')
    val = (balance + amount, total + amount, userID) if updateGain else (balance + amount, total, userID)
    
    cursor.execute(sql, val) # executes the instructions
    db.commit() # saves changes
    cursor.close()
    db.close()
    
    return True

def add_ticket(userID: str, amount: int) -> bool:
    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    
    cursor.execute(f'SELECT tpass FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
    val = cursor.fetchone() # grabs the values of user's balance
    
    try:
        balance = val[0] # balance SHOULD be at index 0
    except:
        balance = 0
    
    sql = ('UPDATE economy SET tpass = ? WHERE user_id = ?')
    val = (balance + amount, userID)
    
    cursor.execute(sql, val) # executes the instructions
    db.commit() # saves changes
    cursor.close()
    db.close()
    
    return True

def remove_money(userID: str, amount: int, updateLoss: bool) -> bool:
    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    
    cursor.execute(f'SELECT balance, loss FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
    val = cursor.fetchone() # grabs the values of user's balance
    
    try:
        balance = val[0] # balance SHOULD be at index 0
        loss = val[1] # loss SHOULD be at index 1
    except:
        balance = 0
        loss = 0
    
    if balance < amount:
        return False
    
    sql = ('UPDATE economy SET balance = ?, loss = ? WHERE user_id = ?')
    val = (balance - amount, loss + amount, userID) if updateLoss else (balance - amount, loss, userID)
    
    cursor.execute(sql, val) # executes the instructions
    db.commit() # saves changes
    cursor.close()
    db.close()
    
    return True

def remove_ticket(userID: str, amount: int) -> bool:
    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    
    cursor.execute(f'SELECT tpass FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
    val = cursor.fetchone() # grabs the values of user's balance
    
    try:
        tpass = val[0] # balance SHOULD be at index 0
    except:
        tpass = 0
    
    if tpass < amount:
        return False
    
    sql = ('UPDATE economy SET tpass = ? WHERE user_id = ?')
    val = (tpass - amount, userID)
    
    cursor.execute(sql, val) # executes the instructions
    db.commit() # saves changes
    cursor.close()
    db.close()
    
    return True

def add_gain(userID: str, amount: int):
    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    
    cursor.execute(f'SELECT total FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
    val = cursor.fetchone() # grabs the values of user's balance
    
    try:
        gain = val[0] # gain SHOULD be at index 0
    except:
        gain = 0
    
    sql = ('UPDATE economy SET total = ? WHERE user_id = ?')
    val = (gain + amount, userID)
    
    cursor.execute(sql, val) # executes the instructions
    db.commit() # saves changes
    cursor.close()
    db.close()
    
    return True

def remove_gain(userID: str, amount: int):
    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    
    cursor.execute(f'SELECT total FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
    val = cursor.fetchone() # grabs the values of user's balance
    
    try:
        gain = val[0] # gain SHOULD be at index 0
    except:
        gain = 0
    
    sql = ('UPDATE economy SET total = ? WHERE user_id = ?')
    val = (gain - amount, userID)
    
    cursor.execute(sql, val) # executes the instructions
    db.commit() # saves changes
    cursor.close()
    db.close()
    
    return True

def add_loss(userID: str, amount: int):
    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    
    cursor.execute(f'SELECT loss FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
    val = cursor.fetchone() # grabs the values of user's balance
    
    try:
        loss = val[0] # gain SHOULD be at index 0
    except:
        loss = 0
    
    sql = ('UPDATE economy SET loss = ? WHERE user_id = ?')
    val = (loss + amount, userID)
    
    cursor.execute(sql, val) # executes the instructions
    db.commit() # saves changes
    cursor.close()
    db.close()
    
    return True

def remove_loss(userID: str, amount: int):
    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    
    cursor.execute(f'SELECT loss FROM economy WHERE user_id = {userID}') # moves cursor to user's balance from database
    val = cursor.fetchone() # grabs the values of user's balance
    
    try:
        loss = val[0] # gain SHOULD be at index 0
    except:
        loss = 0
    
    sql = ('UPDATE economy SET loss = ? WHERE user_id = ?')
    val = (loss - amount, userID)
    
    cursor.execute(sql, val) # executes the instructions
    db.commit() # saves changes
    cursor.close()
    db.close()
    
    return True