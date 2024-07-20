import hikari
import lightbulb
import miru
import random

from bot import get_setting, verify_user, register_user
from utils.economy.manager import EconomyManager

plugin = lightbulb.Plugin('Blackjack')
economy = EconomyManager()

class Deck:
    def __init__(self):
        ranks = ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K']
        suits = [':hearts:', ':diamonds:', ':clubs:', ':spades:']
        self.cards = [{'rank': rank, 'suit': suit} for rank in ranks for suit in suits]
        
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
            rank = card['rank']
            if rank in ['J', 'Q', 'K']:
                score += 10
            elif rank == 'A':
                score += 1
                hasAce = True
            else:
                score += rank
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
            deck.append(f'{card["rank"]}{card["suit"]}')
        return deck
        
class Dealer:
    def __init__(self, deck):
        self.hand = Hand(deck)
            
    def is_busted(self):
        return self.hand.is_busted()
    
    def cards(self):
        deck = []
        for card in self.hand.cards:
            deck.append(f'{card["rank"]}{card["suit"]}')
        return deck

class BlackJackView(miru.View):
    def __init__(self, ctx: lightbulb.Context, embed: hikari.Embed, bet: int, deck: Deck, player: Player, dealer: Dealer) -> None:
        super().__init__(timeout=60.0)
        self.ctx = ctx
        self.embed = embed
        self.author = ctx.author
        self.bet = bet
        self.deck = deck
        self.player = player
        self.dealer = dealer
    
    @miru.button(label='Hit', style=hikari.ButtonStyle.SUCCESS, custom_id='hit')
    async def hit(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self.player.hand.hit()
        self.get_item_by_id(custom_id='double').disabled = True
        
        if self.player.hand.is_busted():
            self.embed.title = 'You Busted!' # Your hand went over 21
            self.embed.description = f"Your hand went over 21 `Bust!`. You lost 🪙 {self.bet}!"
            self.embed.color = get_setting('general', 'embed_error_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            await ctx.edit_response(self.embed, components=[])
            economy.add_loss(self.author.id, self.bet)
            self.stop()
        elif self.player.hand.score() == 21:
            self.embed.title = 'Blackjack! You have won!' # Your hand value is exactly 21
            self.embed.description = f"Your hand was exactly 21. You won 🪙 {self.bet}!"
            self.embed.color = get_setting('general', 'embed_success_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            await ctx.edit_response(self.embed, components=[])
            economy.add_money(ctx.author.id, self.bet*2, True)
            self.stop()
        else:
            self.embed.edit_field(0, "Dealer's Hand", f'{self.dealer.cards()[0]} ?\nValue: ?')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            await ctx.edit_response(self.embed, components=self)
    
    @miru.button(label='Stand', style=hikari.ButtonStyle.PRIMARY, custom_id='stand')
    async def stand(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        while self.dealer.hand.score() < 17:
            self.dealer.hand.hit()
        
        if self.dealer.is_busted():
            self.embed.title = 'Dealer Bust!' # Dealer hand went over 21
            self.embed.description = f"The dealer's hand went over 21, `Bust!`. You won 🪙 {self.bet}!"
            self.embed.color = get_setting('general', 'embed_success_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            economy.add_money(ctx.author.id, self.bet*2, True)
            self.stop()
        elif self.dealer.hand.score() == 21:
            self.embed.title = 'Blackjack! Dealer has won!' # Dealer hand value is exactly 21
            self.embed.description = f"The dealer's hand was exactly 21. You lost 🪙 {self.bet}!"
            self.embed.color = get_setting('general', 'embed_error_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            economy.add_loss(self.author.id, self.bet)
            self.stop()
        elif self.player.hand.score() > self.dealer.hand.score():
            self.embed.title = 'You have won!' # Dealer has less value than you
            self.embed.description = f"The dealer's hand had less value in their cards than your hand. You won 🪙 {self.bet}!"
            self.embed.color = get_setting('general', 'embed_success_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            economy.add_money(ctx.author.id, self.bet*2, True)
            self.stop()
        elif self.player.hand.score() == self.dealer.hand.score():
            self.embed.title = 'Push (Draw)' # Tie
            self.embed.description = f"You and the dealer's hand had the same value of cards."
            self.embed.color = '#FFFF00'
            self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            economy.add_money(ctx.author.id, self.bet, False)
            self.stop()
        else:
            self.embed.title = 'Dealer has won!' # Dealer has more value than you
            self.embed.description = f"The dealer's hand had more value in their cards than your hand. You lost 🪙 {self.bet}!"
            self.embed.color = get_setting('general', 'embed_error_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            economy.add_loss(self.author.id, self.bet)
            self.stop()

        await ctx.edit_response(self.embed, components=[])

    @miru.button(label='Double Down', style=hikari.ButtonStyle.DANGER, custom_id='double')
    async def double(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if economy.remove_money(self.author.id, self.bet, False) == False:
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        self.bet = self.bet * 2
        self.player.hand.hit()

        if self.player.hand.is_busted():
            self.embed.title = 'You Busted!' # Your hand went over 21
            self.embed.description = f"Your hand went over 21 `Bust!`. You lost 🪙 {self.bet}!"
            self.embed.color = get_setting('general', 'embed_error_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            await ctx.edit_response(self.embed, components=[])
            economy.add_loss(self.author.id, self.bet)
            self.stop()
            return
        elif self.player.hand.score() == 21:
            self.embed.title = 'Blackjack! You have won!' # Your hand value is exactly 21
            self.embed.description = f"Your hand was exactly 21. You won 🪙 {self.bet}!"
            self.embed.color = get_setting('general', 'embed_success_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            await ctx.edit_response(self.embed, components=[])
            economy.add_money(ctx.author.id, self.bet*2, True)
            self.stop()
            return
        else:
            self.embed.edit_field(0, "Dealer's Hand", f'{self.dealer.cards()[0]} ?\nValue: ?')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            await ctx.edit_response(self.embed)   

        while self.dealer.hand.score() < 17:
            self.dealer.hand.hit()
        
        if self.dealer.is_busted():
            self.embed.title = 'Dealer Bust!' # Dealer hand went over 21
            self.embed.description = f"The dealer's hand went over 21, `Bust!`. You won 🪙 {self.bet}!"
            self.embed.color = get_setting('general', 'embed_success_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            economy.add_money(ctx.author.id, self.bet*2, True)
            self.stop()
        elif self.dealer.hand.score() == 21:
            self.embed.title = 'Blackjack! Dealer has won!' # Dealer hand value is exactly 21
            self.embed.description = f"The dealer's hand was exactly 21. You lost 🪙 {self.bet}!"
            self.embed.color = get_setting('general', 'embed_error_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            economy.add_loss(self.author.id, self.bet)
            self.stop()
        elif self.player.hand.score() > self.dealer.hand.score():
            self.embed.title = 'You have won!' # Dealer has less value than you
            self.embed.description = f"The dealer's hand had less value in their cards than your hand. You won 🪙 {self.bet}!"
            self.embed.color = get_setting('general', 'embed_success_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            economy.add_money(ctx.author.id, self.bet*2, True)
            self.stop()
        elif self.player.hand.score() == self.dealer.hand.score():
            self.embed.title = 'Push (Draw)' # Tie
            self.embed.description = f"You and the dealer's hand had the same value of cards."
            self.embed.color = '#FFFF00'
            self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            economy.add_money(ctx.author.id, self.bet, False)
            self.stop()
        else:
            self.embed.title = 'Dealer has won!' # Dealer has more value than you
            self.embed.description = f"The dealer's hand had more value in their cards than your hand. You lost 🪙 {self.bet}!"
            self.embed.color = get_setting('general', 'embed_error_color')
            self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
            self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
            self.embed.set_footer(None)
            economy.add_loss(self.author.id, self.bet)
            self.stop()

        await ctx.edit_response(self.embed, components=[])
        
    async def on_timeout(self) -> None:
        self.embed.title = 'Dealer has won!' # Game has timed out
        self.embed.description = f"The game has timed out! You lost 🪙 {self.bet}!"
        self.embed.color = get_setting('general', 'embed_error_color')
        self.embed.edit_field(0, "Dealer's Hand", f'{" ".join(self.dealer.cards())}\nValue: {self.dealer.hand.score()}')
        self.embed.edit_field(1, "Your Hand", f'{" ".join(self.player.cards())}\nValue: {self.player.hand.score()}')
        self.embed.set_footer(None)
        await self.ctx.edit_last_response(self.embed, components=[])
        economy.add_loss(self.author.id, self.bet)
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.author.id

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('bet', 'Number of coins you want to bet.', type=int, min_value=20, max_value=5000, required=True)
@lightbulb.command('blackjack', 'Try your luck in a game of Blackjack against a computer.', aliases=['bj'], pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def blackjack(ctx: lightbulb.Context, bet: int) -> None:
    if verify_user(ctx.user) == None: # if user has never been register
        register_user(ctx.user)
    
    if economy.remove_money(ctx.author.id, bet, False) == False:
        embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    deck = Deck()
    deck.shuffle()
    player = Player(deck)
    dealer = Dealer(deck)
    
    embed = hikari.Embed(title=f'BlackJack!', description=f'Select from `Hit`, `Stand`, or `Double Down`.', color=get_setting('general', 'embed_color'))
    embed.add_field(name="Dealer's Hand", value=f'{dealer.cards()[0]} ?\nValue: ?', inline=True)
    embed.add_field(name="Your Hand", value=f'{" ".join(player.cards())}\nValue: {player.hand.score()}', inline=True)
    embed.set_footer(text='You have 1 minute to choose an action!')

    if player.hand.score() == 21 and dealer.hand.score() == 21:
        embed = hikari.Embed(title=f'Blackjack! Push (Draw)!', description=f'Both hands were exactly 21. You got your bet back.', color='#FFFF00')
        embed.add_field(name="Dealer's Hand", value=f'{" ".join(dealer.cards())}\nValue: {dealer.hand.score()}', inline=True)
        embed.add_field(name="Your Hand", value=f'{" ".join(player.cards())}\nValue: {player.hand.score()}', inline=True)
        economy.add_money(ctx.author.id, bet, False)
        return await ctx.respond(embed)
    elif player.hand.score() == 21:
        embed = hikari.Embed(title=f'Blackjack! You have won!', description=f'Your hand was exactly 21. You won 🪙 {bet}!', color=get_setting('general', 'embed_success_color'))
        embed.add_field(name="Dealer's Hand", value=f'{" ".join(dealer.cards())}\nValue: {dealer.hand.score()}', inline=True)
        embed.add_field(name="Your Hand", value=f'{" ".join(player.cards())}\nValue: {player.hand.score()}', inline=True)
        economy.add_money(ctx.author.id, bet*2, True)
        return await ctx.respond(embed)
    elif dealer.hand.score() == 21:
        embed = hikari.Embed(title=f'Blackjack! Dealer has won!', description=f"The dealer's hand was exactly 21. You lost 🪙 {bet}!", color=get_setting('general', 'embed_error_color'))
        embed.add_field(name="Dealer's Hand", value=f'{" ".join(dealer.cards())}\nValue: {dealer.hand.score()}', inline=True)
        embed.add_field(name="Your Hand", value=f'{" ".join(player.cards())}\nValue: {player.hand.score()}', inline=True)
        economy.remove_money(ctx.author.id, bet, True)
        return await ctx.respond(embed)
    
    view = BlackJackView(ctx, embed, bet, deck, player, dealer)
    
    await ctx.respond(embed, components=view.build())
    client = ctx.bot.d.get('client')
    client.start_view(view)

def load(bot):
    bot.add_plugin(plugin)