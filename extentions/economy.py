import hikari
import lightbulb
import miru
import sqlite3
import random

from datetime import datetime

plugin = lightbulb.Plugin('Enconomy')

## Register New Users to Database ##

@plugin.listener(hikari.MessageCreateEvent)
async def on_message(event: hikari.MessageCreateEvent):
    if event.is_bot or not event.content: # if bot sent the message
        return
    
    user = event.author
    
    db = sqlite3.connect('database.sqlite')
    cursor = db.cursor()
    
    if verify_user(user) == None: # if user has never been register
        sql = ('INSERT INTO database(user_id, balance, total, tpass) VALUES (?, ?, ?, ?)')
        val = (user.id, 100, 100, 0)
        cursor.execute(sql, val) 
    
    db.commit() # saves changes
    cursor.close()
    db.close()

## Balance Command ##

@plugin.command
@lightbulb.add_cooldown(length=10.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.option('user', 'The user to get information about.', type=hikari.User, required=False)
@lightbulb.command('balance', 'Get balance on a server member.', aliases=['bal'], pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def balance(ctx: lightbulb.SlashContext, user: hikari.User) -> None:
    if user == None: # if no user has been sent
        user = ctx.author
    elif user.is_bot: # user has been sent. checks if user is a bot
        embed = hikari.Embed(description="Bots don't have the rights to earn money!", color='#FF0000')
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    username = user.username
    
    db = sqlite3.connect('database.sqlite')
    cursor = db.cursor()
    
    cursor.execute(f'SELECT balance, total, tpass FROM database WHERE user_id = {user.id}') # moves cursor to user's balance, total, and tpass from database
    bal = cursor.fetchone() # grabs the values of user's balance and total
    
    try: # just in case for errors
        balance = bal[0] # balance SHOULD be at index 0
        total = bal[1] # total SHOULD be at index 1
        tpass = bal[2] # tpass SHOULD be at index 2
    except:
        balance = 0
        total = 0
        tpass = 0
    
    cursor.close()
    db.close()
    
    embed = (
        hikari.Embed(title=f"{username}'s Balance", description=f'Coins: 🪙 {balance}\nTotal Earnings: 🪙 {total}\nTux Pass: {tpass} 🎟️', color='#249EDB', timestamp=datetime.now().astimezone())
        .set_footer(text=f'Requested by {ctx.author.username}', icon=ctx.author.display_avatar_url)
        .set_thumbnail(user.avatar_url)
    )
    
    await ctx.respond(embed)

## Daily Command ##

@plugin.command
@lightbulb.add_cooldown(length=86400.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.command('daily', 'Get your daily reward!')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def daily(ctx: lightbulb.Context) -> None:
    user = ctx.author
    earnings = random.randint(50,300)
    
    db = sqlite3.connect('database.sqlite')
    cursor = db.cursor()
    
    if verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color='#FF0000')
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    cursor.execute(f'SELECT balance, total FROM database WHERE user_id = {user.id}') # moves cursor to user's balance from database
    bal = cursor.fetchone() # grabs the value of user's balance
    
    try: # just in case for errors
        balance = bal[0] # balance SHOULD be at index 0
        total = bal[1] # total SHOULD be at index 1
    except:
        balance = 0
        total = 0
    
    sql = ('UPDATE database SET balance = ?, total = ? WHERE user_id = ?') # update user's new balance and total in database
    val = (balance + earnings, total + earnings, user.id)
    cursor.execute(sql, val) # executes the instructions
    
    embed = (hikari.Embed(description=f'You earned 🪙 {earnings}!', color='#249EDB'))
    await ctx.respond(embed)
    
    db.commit() # saves changes
    cursor.close()
    db.close()

## Pay Command ##

@plugin.command
@lightbulb.add_cooldown(length=10.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.option('number', 'Number of coins', type=int, min_value=1, max_value=None, required=True)
@lightbulb.option('user', 'The user you are about to pay.', type=hikari.User, required=True)
@lightbulb.command('pay', 'Give a server member money!', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def pay(ctx: lightbulb.SlashContext, user: hikari.User, number: int) -> None:
    if user.is_bot or ctx.author.id == user.id: # checks if the user is a bot or the sender
        embed = hikari.Embed(description='You are not allowed to send money to this user!', color='#FF0000')
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    sender = ctx.author
    userUsername = user.username
    
    db = sqlite3.connect('database.sqlite')
    cursor = db.cursor()

    if verify_user(sender) == None: # if user has never been register
        embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color='#FF0000')
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description='User does not have a balance! Let the user know to type in chat at least once!', color='#FF0000')
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    cursor.execute(f'SELECT balance FROM database WHERE user_id = {sender.id}') # moves cursor to sender's balance from database
    senderBal = cursor.fetchone() # grabs the value of sender's balance
    
    cursor.execute(f'SELECT balance FROM database WHERE user_id = {user.id}') # moves cursor to user's balance from database
    userBal = cursor.fetchone() # grabs the value of user's balance
    
    try: # just in case for errors
        senderBalance = senderBal[0] # balance SHOULD be at index 0
        userBalance = userBal[0] # balance SHOULD be at index 0
    except:
        senderBalance = 0
        userBalance = 0
    
    if senderBalance < number: # checks if sender has enough money to send the specified amount
        embed = hikari.Embed(description='You do not have enough money!', color='#FF0000')
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    sql = ('UPDATE database SET balance = ? WHERE user_id = ?') # update sender's new balance in database
    val = (senderBalance - number, sender.id)
    cursor.execute(sql, val) # executes the instructions
    
    sql = ('UPDATE database SET balance = ? WHERE user_id = ?') # update user's new balance in database
    val = (userBalance + number, user.id)
    cursor.execute(sql, val) # executes the instructions
    
    embed = (hikari.Embed(description=f'You sent 🪙 {number} to {userUsername}!', color='#249EDB'))
    await ctx.respond(embed)
    
    db.commit() # saves changes
    cursor.close()
    db.close()

## Coinflip Command ##

@plugin.command
@lightbulb.add_cooldown(length=10.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.option('number', 'Number of coinflip(s)', type=int, min_value=1, max_value=100, required=True)
@lightbulb.command('coinflip', 'Flips a coin!', pass_options=True)
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

    embed = (hikari.Embed(title='Coinflip Result(s):', description=result, color='#249EDB'))
    embed.add_field('Summary:', f'Heads: {heads} Tails: {tails}')
    await ctx.respond(embed)

## Battle Command ##

@plugin.command
@lightbulb.add_cooldown(length=60, uses=10, bucket=lightbulb.UserBucket)
@lightbulb.option('bet', 'Number of coins you want to bet', type=int, min_value=10, max_value=200, required=True)
@lightbulb.command('battle', 'Draw a card against a bot. Winner has the highest value card.', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def battle(ctx: lightbulb.Context, bet: int) -> None:
    cards = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    patterns = ['♥️', '♠️', '♣️', '♦️']
    playerCard = [cards[random.randint(0,13)], patterns[random.randint(0,3)]]
    botCard = [cards[random.randint(0,13)], patterns[random.randint(0,3)]]

    user = ctx.author
    
    if verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color='#FF0000')
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    db = sqlite3.connect('database.sqlite')
    cursor = db.cursor()
    
    cursor.execute(f'SELECT balance, total FROM database WHERE user_id = {user.id}') # moves cursor to user's balance from database
    bal = cursor.fetchone() # grabs the value of user's balance
    
    try: # just in case for errors
        balance = bal[0] # balance SHOULD be at index 0
        total = bal[1] # total SHOULD be at index 1
    except:
        balance = 0
        total = 0
    
    if balance < bet: # checks if sender has enough money to send the specified amount
        embed = hikari.Embed(description='You do not have enough money!', color='#FF0000')
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    sql = ('UPDATE database SET balance = ?, total = ? WHERE user_id = ?') # update user's new balance and total in database
    
    if botCard[0] > playerCard[0]:
        val = (balance - (bet), total, user.id)
        embed = (hikari.Embed(title='FUCK YOU', description=f"Your card: {playerCard[0]}{playerCard[1]}\nDealer's card: {botCard[0]}{botCard[1]}\n\nYou lost 🪙 {bet}!", color='#FF0000')) 
    elif botCard[0] < playerCard[0]:
        val = (balance + (bet * 2), total + (bet * 2), user.id)
        embed = (hikari.Embed(title='You win... for now 😬', description=f"Your card: {playerCard[0]}{playerCard[1]}\nDealer's card: {botCard[0]}{botCard[1]}\n\nYou won 🪙 {bet * 2}!", color='#32CD32'))
    else:
        val = (balance, total, user.id)
        embed = (hikari.Embed(title='Draw', description=f"Your card: {playerCard[0]}{playerCard[1]}\nDealer's card: {botCard[0]}{botCard[1]}", color='#FFFF00'))

    cursor.execute(sql, val) # executes the instructions
    db.commit() # saves changes
    cursor.close()
    db.close()
    
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
@lightbulb.add_cooldown(length=10.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.command('draw', 'Draw a card from a deck.')
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

    embed = hikari.Embed(title=f'Cards Remaining: {len(deck)}', description=f"Your card: {get_card_str(card)}", color='#249EDB')
    message = await ctx.respond(embed,components=view.build())
    message = await message
    
    view.start(message)
    await view.wait()

    while True:
        if hasattr(view, 'action'):
            match view.action:
                case 'Draw':
                    if len(deck) >= 1:
                        card = get_card(deck)
                        deck.remove(card)
                        embed = hikari.Embed(title=f'Cards Remaining: {len(deck)}', description=f"Your card: {get_card_str(card)}", color='#249EDB')
                    else:
                        return await ctx.edit_last_response(hikari.Embed(description=f"There are no more cards in this deck.", color='#249EDB'))
                case 'Draw 5':
                    if len(deck) >= 5:
                        cards = []
                        for i in range(5):
                            card = get_card(deck)
                            cards.append(get_card_str(card))
                            deck.remove(card)
                        embed = hikari.Embed(title=f'Cards Remaining: {len(deck)}', description=f"Your cards: {', '.join(cards)}", color='#249EDB')
                    elif len(deck) < 5 and len(deck) > 0:
                        cards = []
                        for i in range(len(deck)):
                            card = get_card(deck)
                            cards.append(get_card_str(card))
                            deck.remove(card)
                        embed = hikari.Embed(title=f'Cards Remaining: {len(deck)}', description=f"Your cards: {', '.join(cards)}", color='#249EDB')
                    else:
                        return await ctx.edit_last_response(hikari.Embed(description=f"There are no more cards in this deck.", color='#249EDB'))
        else:
            embed = hikari.Embed(description=f"Menu has closed due to inactivity.", color='#249EDB')
            await ctx.edit_last_response(embed, components=[])
            return
        
        view = CheckView(player)
        view.add_item(DrawButton())
        view.add_item(Draw5Button())
        message = await ctx.edit_last_response(embed, components=view.build())
        view.start(message)
        await view.wait()

def get_card(cards):
    card = cards[random.randint(0,len(cards)-1)]
    return card

def get_card_str(card):
    string = ''.join(card.split(' '))
    return string

def verify_user(user):
    db = sqlite3.connect('database.sqlite')
    cursor = db.cursor()
    
    cursor.execute(f'SELECT user_id FROM database WHERE user_id = {user.id}') # moves cursor to user's id from database
    result = cursor.fetchone() # grabs the value of user's id
    
    return result

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