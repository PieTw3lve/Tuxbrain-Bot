import hikari
import lightbulb
import miru
import random

from io import BytesIO
from PIL import Image

from bot import get_setting, verify_user, register_user
from utils.economy.manager import EconomyManager

plugin = lightbulb.Plugin('Hi-Lo')
economy = EconomyManager()
        
class Player:
    def __init__(self, deck):
        self.hand = Hand(deck)

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
    
    def display(self, player: Player, dealer: Player, hidden: bool = False) -> bytes:
        table = Image.open(self.TABLE_IMAGE_PATH).convert('RGBA')

        playerCardPath = self.CARD_IMAGE_PATH.format(suit=str(player.hand.cards[0]["suit"]).replace(":", ""), rank=player.hand.score())
        playerCard = Image.open(playerCardPath).convert('RGBA')

        if hidden:
            dealerCard = Image.open(self.BACK_IMAGE_PATH).convert('RGBA')
        else:
            dealerCardPath = self.CARD_IMAGE_PATH.format(suit=str(dealer.hand.cards[0]["suit"]).replace(":", ""), rank=dealer.hand.score())
            dealerCard = Image.open(dealerCardPath).convert('RGBA')

        table.paste(playerCard, (162, 158), playerCard)
        table.paste(dealerCard, (532, 158), dealerCard)

        with BytesIO() as a:
            table.save(a, 'PNG')
            a.seek(0)
            return a.getvalue()

class Hand:
    values = {'A': 1, 'J': 11, 'Q': 12, 'K': 13}
    multipliers = {
        1: {'hi': 1, 'lo': 0},
        2: {'hi': 1.1, 'lo': 10.7},
        3: {'hi': 1.1, 'lo': 5.3},
        4: {'hi': 1.1, 'lo': 3.5},
        5: {'hi': 1.3, 'lo': 2.6},
        6: {'hi': 1.5, 'lo': 2.1},
        7: {'hi': 1.87, 'lo': 1.87},
        8: {'hi': 2.1, 'lo': 1.5},
        9: {'hi': 2.6, 'lo': 1.3},
        10: {'hi': 3.5, 'lo': 1.1},
        11: {'hi': 5.3, 'lo': 1.1},
        12: {'hi': 10.7, 'lo': 1.1},
        13: {'hi': 0, 'lo': 1}
    }
    
    def __init__(self, deck: Deck):
        self.deck = deck
        self.cards = [deck.draw()]
        self.switch = False
    
    def score(self):
        return sum(self.values.get(card['rank'], card['rank']) for card in self.cards)
    
    def payout(self, option: str) -> int:
        return self.multipliers[self.score()][option]
    
    def switch_card(self):
        card, position = self.cards.pop(), random.randint(0, len(self.deck.cards))
        self.deck.cards.insert(position, card)
        self.cards.append(self.deck.draw())
        self.switch = True
    
    def next_round(self):
        self.cards.clear()
        self.cards.append(self.deck.draw())

class ContinueView(miru.View):
    def __init__(self, ctx: lightbulb.Context, embed: hikari.Embed, bet: int, deck: Deck, player: Player, dealer: Player, round: int, switch: bool) -> None:
        super().__init__(timeout=60.0)
        self.ctx = ctx
        self.embed = embed
        self.author = ctx.author
        self.bet = bet
        self.deck = deck
        self.player = player
        self.dealer = dealer
        self.round = round
        self.switch = switch

    @miru.button('Next Round', style=hikari.ButtonStyle.SUCCESS, custom_id='continue')
    async def on_continue(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self.player.hand.next_round()
        self.dealer.hand.next_round()
        self.embed.title = f'Round {self.round}: Higher or Lower?'
        self.embed.description = (
            f"Do you think the dealer's card will be higher or lower? You can also switch your card for a new card, but this can only be used once.\n\n"
            f'> **Your Bet**: {self.bet:,} 🪙\n'
            f'> **Payout Multiplier (Higher)**: x{self.player.hand.payout("hi")}\n'
            f'> **Payout Multiplier (Lower)**: x{self.player.hand.payout("lo")}\n'
        )
        self.embed.color = get_setting('general', 'embed_color')
        self.embed.set_image(self.deck.display(self.player, self.dealer, True))
        await self.switch_view(ctx)

    @miru.button('Cash Out', style=hikari.ButtonStyle.DANGER, custom_id='cash_out')
    async def on_cash_out(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        economy.add_money(self.author.id, self.bet, True)
        self.embed.title = f'Cashed Out!'
        self.embed.description = (
            f'You cashed out your winnings.\n\n'
            f'> **Total Rounds**: {self.round}\n'
            f'> **Payout Winnings**: {self.bet:,} 🪙\n'
        )
        self.embed.color = get_setting('general', 'embed_success_color')
        self.embed.set_footer(None)
        await ctx.edit_response(embed=self.embed, components=[])
        self.stop()

    async def switch_view(self, ctx: miru.ViewContext) -> None:
        self.stop()
        view = HiLoView(self.ctx, self.embed, self.bet, self.deck, self.player, self.dealer, self.round, self.switch)
        await ctx.edit_response(embed=self.embed, components=view.build())
        self.client.start_view(view)

    async def on_timeout(self) -> None:
        economy.add_money(self.author.id, self.bet, True)
        self.embed.title = f'Cashed Out!'
        self.embed.description = (
            f'You cashed out your winnings.\n\n'
            f'> **Total Rounds**: {self.round}\n'
            f'> **Payout Winnings**: {self.bet:,} 🪙\n'
        )
        self.embed.color = get_setting('general', 'embed_success_color')
        self.embed.set_footer(None)
        await self.ctx.edit_last_response(embed=self.embed, components=[])

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.author.id

class HiLoView(miru.View):
    def __init__(self, ctx: lightbulb.Context, embed: hikari.Embed, bet: int, deck: Deck, player: Player, dealer: Player, round: int = 1, switch: bool = False) -> None:
        super().__init__(timeout=300.0)
        self.ctx = ctx
        self.embed = embed
        self.author = ctx.author
        self.bet = bet
        self.deck = deck
        self.player = player
        self.dealer = dealer
        self.round = round
        self.switch = switch
        self.update_buttons()

    async def handle_result(self, ctx: miru.ViewContext, won: bool, payout: int, option: str, push: bool = False) -> None:
        if push:
            self.embed.title = f'Round {self.round}: Push (Draw)!'
            self.embed.description = (
                f'Your bet is returned.\n\n'
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x1\n'
                f'> **Payout Winnings**: {self.bet:,} 🪙\n'
            )
            self.embed.color = '#FFFF00'
            self.embed.set_image(self.deck.display(self.player, self.dealer))
            await self.switch_view(ctx)
        elif won:
            self.embed.title = f'Round {self.round}: You guessed correctly!'
            self.embed.description = (
                f'You can either cash out or continue to the next round with your winnings.\n\n'
                f'> **Your Bet**: {self.bet:,} 🪙\n'
                f'> **Payout Multiplier**: x{self.player.hand.payout(option)}\n'
                f'> **Payout Winnings**: {payout:,} 🪙\n'
            )
            self.embed.color = get_setting('general', 'embed_success_color')
            self.embed.set_image(self.deck.display(self.player, self.dealer))
            self.bet = payout
            await self.switch_view(ctx)
        else:
            economy.add_loss(self.author.id, self.bet)
            self.embed.title = f'You guessed incorrectly!'
            self.embed.description = (
                f'Better luck next time.\n\n'
                f'> **Total Rounds**: {self.round}\n'
                f'> **Your Bet**: {self.bet:,} 🪙\n'
            )
            self.embed.color = get_setting('general', 'embed_error_color')
            self.embed.set_image(self.deck.display(self.player, self.dealer))
            self.embed.set_footer(None)
            await ctx.edit_response(embed=self.embed, components=[])
            self.stop()

    @miru.button('Higher', style=hikari.ButtonStyle.PRIMARY, custom_id='higher')
    async def on_higher(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        payout = round(self.bet * self.player.hand.payout('hi'))
        if self.player.hand.score() == self.dealer.hand.score():
            await self.handle_result(ctx, False, payout, 'hi', True)
        else:
            won = self.player.hand.score() < self.dealer.hand.score()
            await self.handle_result(ctx, won, payout, 'hi')

    @miru.button('Lower', style=hikari.ButtonStyle.PRIMARY, custom_id='lower')
    async def on_lower(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        payout = round(self.bet * self.player.hand.payout('lo'))
        if self.player.hand.score() == self.dealer.hand.score():
            await self.handle_result(ctx, False, payout, 'lo', True)
        else:
            won = self.player.hand.score() > self.dealer.hand.score()
            await self.handle_result(ctx, won, payout, 'lo')

    @miru.button('Switch', style=hikari.ButtonStyle.SECONDARY, custom_id='switch')
    async def on_switch(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self.switch = True
        self.player.hand.switch_card()
        self.update_buttons()
        self.embed.description = (
            f"Do you think the dealer's card will be higher or lower? You can also switch your card for a new card, but this can only be used once.\n\n"
            f'> **Your Bet**: {self.bet:,} 🪙\n'
            f'> **Payout Multiplier (Higher)**: x{self.player.hand.payout("hi")}\n'
            f'> **Payout Multiplier (Lower)**: x{self.player.hand.payout("lo")}\n'
        )
        self.embed.set_image(self.deck.display(self.player, self.dealer, True))
        await ctx.edit_response(embed=self.embed, components=self.build())

    async def switch_view(self, ctx: miru.ViewContext) -> None:
        self.stop()
        view = ContinueView(self.ctx, self.embed, self.bet, self.deck, self.player, self.dealer, self.round + 1, self.get_item_by_id(custom_id='switch').disabled)
        await ctx.edit_response(embed=self.embed, components=view.build())
        self.client.start_view(view)

    async def on_timeout(self) -> None:
        economy.add_loss(self.author.id, self.bet)
        self.embed.description = (
            f'Game has timed out!\n\n'
            f'> **Total Rounds**: {self.round}\n'
            f'> **Payout Winnings**: 0 🪙\n'
        )
        self.embed.color = get_setting('general', 'embed_error_color')
        self.embed.set_image(self.deck.display(self.player, self.dealer))
        self.embed.set_footer(None)
        await self.ctx.edit_last_response(embed=self.embed, components=[])
        self.stop()

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.author.id
    
    def update_buttons(self) -> None:
        self.get_item_by_id(custom_id='higher').disabled = True if self.player.hand.score() == 13 else False
        self.get_item_by_id(custom_id='lower').disabled = True if self.player.hand.score() == 1 else False
        self.get_item_by_id(custom_id='switch').disabled = self.switch

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('bet', 'Number of coins you want to bet.', type=int, min_value=10, max_value=1000, required=True)
@lightbulb.command('hi-lo', 'Try your luck in a game of Higher-Lower.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def hi_lo(ctx: lightbulb.Context, bet: int) -> None:
    if verify_user(ctx.user) == None: # if user has never been register
        register_user(ctx.user)

    if economy.remove_money(ctx.author.id, bet, False) == False:
        embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    
    deck = Deck()
    deck.shuffle()
    player, dealer = Player(deck), Player(deck)

    embed = hikari.Embed(
        title='Round 1: Higher or Lower?',
        description=f"Do you think the dealer's card will be higher or lower? You can also switch your card for a new card, but this can only be used once.\n\n"
                    f'> **Your Bet**: {bet} 🪙\n'
                    f'> **Payout Multiplier (Higher)**: x{player.hand.payout("hi")}\n'
                    f'> **Payout Multiplier (Lower)**: x{player.hand.payout("lo")}\n',
        color=get_setting('general', 'embed_color')
    )
    embed.set_image(deck.display(player, dealer, True))
    embed.set_footer(text='You have 5 minutes to choose an action!')

    view = HiLoView(ctx, embed, bet, deck, player, dealer)

    await ctx.respond(embed, components=view.build())
    client = ctx.bot.d.get('client')
    client.start_view(view)

def load(bot):
    bot.add_plugin(plugin)