import hikari
import lightbulb
import miru
import random

from bot import get_setting

plugin = lightbulb.Plugin('Draw')

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
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('draw', 'Draw cards from a deck.')
@lightbulb.implements(lightbulb.SlashCommand)
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

    embed = hikari.Embed(title=f'Cards Remaining: {len(deck)}', description=f"Your card: {get_card_str(card)}", color=get_setting('settings', 'embed_color'))
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
                        embed = hikari.Embed(title=f'Cards Remaining: {len(deck)}', description=f"Your card: {get_card_str(card)}", color=get_setting('settings', 'embed_color'))
                    else:
                        return await ctx.edit_last_response(hikari.Embed(description=f"There are no more cards in this deck.", color=get_setting('settings', 'embed_color')))
                case 'Draw 5':
                    if len(deck) >= 5:
                        cards = []
                        for i in range(5):
                            card = get_card(deck)
                            cards.append(get_card_str(card))
                            deck.remove(card)
                        embed = hikari.Embed(title=f'Cards Remaining: {len(deck)}', description=f"Your cards: {', '.join(cards)}", color=get_setting('settings', 'embed_color'))
                    elif len(deck) < 5 and len(deck) > 0:
                        cards = []
                        for i in range(len(deck)):
                            card = get_card(deck)
                            cards.append(get_card_str(card))
                            deck.remove(card)
                        embed = hikari.Embed(title=f'Cards Remaining: {len(deck)}', description=f"Your cards: {', '.join(cards)}", color=get_setting('settings', 'embed_color'))
                    else:
                        return await ctx.edit_last_response(hikari.Embed(description=f"There are no more cards in this deck.", color=get_setting('settings', 'embed_color')))
        else:
            embed = hikari.Embed(description=f"Menu has closed due to inactivity.", color=get_setting('settings', 'embed_color'))
            await ctx.edit_last_response(embed, components=[])
            return
        
        view = CheckView(player)
        view.add_item(DrawButton())
        view.add_item(Draw5Button())
        message = await ctx.edit_last_response(embed, components=view.build())
        await view.start(message)
        await view.wait()

def get_card(cards):
    card = cards[random.randint(0,len(cards)-1)]
    return card

def get_card_str(card):
    string = ''.join(card.split(' '))
    return string

def load(bot):
    bot.add_plugin(plugin)