from cmath import cos, sin
from math import radians
import hikari
import lightbulb
import miru
import random

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from bot import get_setting, verify_user, register_user
from utils.economy.manager import EconomyManager

plugin = lightbulb.Plugin('Blackjack')
economy = EconomyManager()
    
class Player:
    def __init__(self, deck):
        self.hand = Hand(deck)
                
    def is_busted(self):
        return self.hand.is_busted()

class Deck:
    CARD_IMAGE_PATH = 'assets/img/economy/casino/{suit}/{rank}.png'
    BACK_IMAGE_PATH = 'assets/img/economy/casino/back.png'
    TABLE_IMAGE_PATH = 'assets/img/economy/casino/table.png'

    def __init__(self):
        ranks = ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K']
        suits = [':hearts:', ':diamonds:', ':clubs:', ':spades:']
        self.cards = [{'rank': rank, 'suit': suit} for rank in ranks for suit in suits]
        
    def shuffle(self):
        random.shuffle(self.cards)
        
    def draw(self):
        return self.cards.pop()
    
    def display(self, player: Player, dealer: Player, hidden: bool = False):
        table = Image.open(self.TABLE_IMAGE_PATH).convert('RGBA')
        playerCards = []
        dealerCards = []

        def rank_to_number(rank):
            if rank == 'A':
                return '1'
            elif rank == 'J':
                return '11'
            elif rank == 'Q':
                return '12'
            elif rank == 'K':
                return '13'
            return str(rank)

        for card in player.hand.cards:
            rank = rank_to_number(card['rank'])
            cardImage = Image.open(self.CARD_IMAGE_PATH.format(suit=str(card['suit']).replace(":", ""), rank=rank)).convert('RGBA')
            playerCards.append(cardImage)
        for card in dealer.hand.cards:
            rank = rank_to_number(card['rank'])
            cardImage = Image.open(self.CARD_IMAGE_PATH.format(suit=str(card['suit']).replace(":", ""), rank=rank)).convert('RGBA')
            if len(dealerCards) < 1 or not hidden:
                dealerCards.append(cardImage)
            else:
                dealerCards.append(Image.open(self.BACK_IMAGE_PATH).convert('RGBA'))

        def paste_cards(canvas, cards, x, y, offset = 50):
            width = (len(cards) - 1) * offset
            startX = x - width // 2

            for i, card in enumerate(cards):
                x = startX + i * offset
                canvas.paste(card, (x, y), card)
            
        paste_cards(table, playerCards, 162, 158)
        paste_cards(table, dealerCards, 532, 158)

        draw = ImageDraw.Draw(table)
        font = ImageFont.truetype('assets/font/CannedPixels.ttf', size=80)
        draw.text((220, 390), str(player.hand.score()), font=font, fill=(255, 255, 255), anchor='mm', align='center')
        draw.text((590, 390), str(dealer.hand.score()) if not hidden else '?', font=font, fill=(255, 255, 255), anchor='mm', align='center')

        with BytesIO() as a:
            table.save(a, 'PNG')
            a.seek(0)
            return a.getvalue()

class Hand:
    def __init__(self, deck: Deck):
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
    
class BlackJackView(miru.View):
    def __init__(self, ctx: lightbulb.Context, embed: hikari.Embed, bet: int, deck: Deck, player: Player, dealer: Player) -> None:
        super().__init__(timeout=300.0)
        self.ctx = ctx
        self.embed = embed
        self.author = ctx.author
        self.bet = bet
        self.deck = deck
        self.player = player
        self.dealer = dealer

    async def end_game(self, title, description, color, won = False, draw = False):
        self.embed.title = title
        self.embed.description = description
        self.embed.color = color
        self.embed.set_image(self.deck.display(self.player, self.dealer))
        self.embed.set_footer(None)
        await self.ctx.edit_last_response(self.embed, components=[])
        if won:
            economy.add_money(self.author.id, self.bet * 2, False)
            economy.add_gain(self.author.id, self.bet)
        elif draw:
            economy.add_money(self.author.id, self.bet, False)
        else:
            economy.add_loss(self.author.id, self.bet)
        self.stop()
    
    @miru.button(label='Hit', style=hikari.ButtonStyle.SUCCESS, custom_id='hit')
    async def hit(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self.player.hand.hit()
        self.get_item_by_id(custom_id='double').disabled = True
        
        if self.player.hand.is_busted():
            await self.end_game(
                'You Busted!', 
                f"Your hand went over 21, bust!\n\n"
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x2\n'
                f'> **Payout Winnings**: 0 🪙',
                get_setting('general', 'embed_error_color')
            )
        elif self.player.hand.score() == 21:
            await self.end_game(
                'Blackjack! You have won!', 
                f"Your hand was exactly 21!\n\n"
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x2\n'
                f'> **Payout Winnings**: {self.bet * 2:,} 🪙',
                get_setting('general', 'embed_success_color'),
                won=True
            )
        else:
            self.embed.set_image(self.deck.display(self.player, self.dealer, True))
            await ctx.edit_response(self.embed, components=self)
    
    @miru.button(label='Stand', style=hikari.ButtonStyle.PRIMARY, custom_id='stand')
    async def stand(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        while self.dealer.hand.score() < 17:
            self.dealer.hand.hit()
        
        if self.dealer.is_busted():
            await self.end_game(
                'Dealer Bust!', 
                f"The dealer's hand went over 21, bust!\n\n"
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x2\n'
                f'> **Payout Winnings**: {self.bet * 2:,} 🪙',
                get_setting('general', 'embed_success_color'),
                won=True
            )
        elif self.dealer.hand.score() == 21:
            await self.end_game(
                'Blackjack! Dealer has won!', 
                f"The dealer's hand was exactly 21!\n\n"
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x2\n'
                f'> **Payout Winnings**: 0 🪙',
                get_setting('general', 'embed_error_color')
            )
        elif self.player.hand.score() > self.dealer.hand.score():
            await self.end_game(
                'You have won!', 
                f"The dealer's hand had less value in their cards than your hand.\n\n"
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x2\n'
                f'> **Payout Winnings**: {self.bet * 2:,} 🪙',
                get_setting('general', 'embed_success_color'),
                won=True
            )
        elif self.player.hand.score() == self.dealer.hand.score():
            await self.end_game(
                'Push (Draw)', 
                f"You and the dealer's hand had the same value of cards.\n\n"
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x1\n'
                f'> **Payout Winnings**: {self.bet:,} 🪙',
                '#FFFF00',
                draw=True
            )
        else:
            await self.end_game(
                'Dealer has won!', 
                f"The dealer's hand had more value in their cards than your hand.\n\n"
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x2\n'
                f'> **Payout Winnings**: 0 🪙',
                get_setting('general', 'embed_error_color')
            )

    @miru.button(label='Double Down', style=hikari.ButtonStyle.DANGER, custom_id='double')
    async def double(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if economy.remove_money(self.author.id, self.bet, False) == False:
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        self.bet = self.bet * 2
        self.player.hand.hit()

        if self.player.hand.is_busted():
            await self.end_game(
                'You Busted!', 
                f"Your hand went over 21, bust!\n\n"
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x2\n'
                f'> **Payout Winnings**: 0 🪙',
                get_setting('general', 'embed_error_color')
            )
            return
        elif self.player.hand.score() == 21:
            await self.end_game(
                'Blackjack! You have won!', 
                f"Your hand was exactly 21!\n\n"
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x2\n'
                f'> **Payout Winnings**: {self.bet * 2:,} 🪙',
                get_setting('general', 'embed_success_color'),
                won=True
            )
            return
        else:
            self.embed.set_image(self.deck.display(self.player, self.dealer, True))
            await ctx.edit_response(self.embed)   

        while self.dealer.hand.score() < 17:
            self.dealer.hand.hit()
        
        if self.dealer.is_busted():
            await self.end_game(
                'Dealer Bust!', 
                f"The dealer's hand went over 21, bust!.\n\n"
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x2\n'
                f'> **Payout Winnings**: {self.bet * 2:,} 🪙',
                get_setting('general', 'embed_success_color'),
                won=True
            )
        elif self.dealer.hand.score() == 21:
            await self.end_game(
                'Blackjack! Dealer has won!', 
                f"The dealer's hand was exactly 21!\n\n"
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x2\n'
                f'> **Payout Winnings**: 0 🪙',
                get_setting('general', 'embed_error_color')
            )
        elif self.player.hand.score() > self.dealer.hand.score():
            await self.end_game(
                'You have won!', 
                f"The dealer's hand had less value in their cards than your hand.\n\n"
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x2\n'
                f'> **Payout Winnings**: {self.bet * 2:,} 🪙',
                get_setting('general', 'embed_success_color'),
                won=True
            )
        elif self.player.hand.score() == self.dealer.hand.score():
            await self.end_game(
                'Push (Draw)', 
                f"You and the dealer's hand had the same value of cards.\n\n"
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x1\n'
                f'> **Payout Winnings**: {self.bet:,} 🪙',
                '#FFFF00',
                draw=True
            )
        else:
            await self.end_game(
                'Dealer has won!', 
                f"The dealer's hand had more value in their cards than your hand.\n\n"
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x2\n'
                f'> **Payout Winnings**: 0 🪙',
                get_setting('general', 'embed_error_color')
            )

    async def on_timeout(self) -> None:
        await self.end_game(
            'Dealer has won!', 
            f"The game has timed out!\n\n"
            f'> **Your Bet**: {self.bet:,} 🪙\n'
            f'> **Payout Multiplier**: x2\n'
            f'> **Payout Winnings**: 0 🪙',
            get_setting('general', 'embed_error_color')
        )
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.author.id

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('bet', 'Number of coins you want to bet.', type=int, min_value=10, max_value=5000, required=True)
@lightbulb.command('blackjack', 'Try your luck in a game of Blackjack.', aliases=['bj'], pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def blackjack(ctx: lightbulb.Context, bet: int) -> None:
    if verify_user(ctx.user) == None: # if user has never been register
        register_user(ctx.user)
    
    if economy.remove_money(ctx.author.id, bet, False) == False:
        embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    deck = Deck()
    deck.shuffle()
    player, dealer = Player(deck), Player(deck)
    
    embed = hikari.Embed(
        title=f'BlackJack!', 
        description=f'Try getting as close to 21 without going over! Press hit to draw a card, stand to end your turn, or double down to double your bet and draw one more card.\n\n'
                    f'> **Your Bet**: {bet:,} 🪙\n'
                    f'> **Payout Multiplier**: x2\n'
                    f'> **Payout Winnings**: {bet * 2:,} 🪙',
        color=get_setting('general', 'embed_color')
    )
    embed.set_image(deck.display(player, dealer, True))
    embed.set_footer(text='You have 5 minute to choose an action!')

    if player.hand.score() == 21 and dealer.hand.score() == 21:
        embed = hikari.Embed(
            title=f'Blackjack! Push (Draw)!', 
            description=f'Both hands were exactly 21! You got your bet back.\n\n'
                        f'> **Your Bet**: {bet:,} 🪙\n'
                        f'> **Payout Multiplier**: x1\n'
                        f'> **Payout Winnings**: {bet:,} 🪙',
            color='#FFFF00'
        )
        embed.set_image(deck.display(player, dealer))
        economy.add_money(ctx.author.id, bet, False)
        return await ctx.respond(embed)
    elif player.hand.score() == 21:
        embed = hikari.Embed(
            title=f'Blackjack! You have won!', 
            description=f'Your hand was exactly 21!\n\n'
                        f'> **Your Bet**: {bet:,} 🪙\n'
                        f'> **Payout Multiplier**: x2\n'
                        f'> **Payout Winnings**: {bet * 2:,} 🪙',
            color=get_setting('general', 'embed_success_color')
        )
        embed.set_image(deck.display(player, dealer))
        economy.add_money(ctx.author.id, bet*2, False)
        economy.add_gain(ctx.author.id, bet)
        return await ctx.respond(embed)
    elif dealer.hand.score() == 21:
        embed = hikari.Embed(
            title=f'Blackjack! Dealer has won!', 
            description=f"The dealer's hand was exactly 21!\n\n"
                        f'> **Your Bet**: {bet:,} 🪙\n'
                        f'> **Payout Multiplier**: x2\n'
                        f'> **Payout Winnings**: 0 🪙',
            color=get_setting('general', 'embed_error_color')
        )
        embed.set_image(deck.display(player, dealer))
        economy.add_loss(ctx.author.id, bet)
        return await ctx.respond(embed)
    
    view = BlackJackView(ctx, embed, bet, deck, player, dealer)
    
    await ctx.respond(embed, components=view.build())
    client = ctx.bot.d.get('client')
    client.start_view(view)

def load(bot):
    bot.add_plugin(plugin)