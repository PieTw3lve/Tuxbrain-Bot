import hikari
import miru
import random

from datetime import datetime
from miru.context.view import ViewContext

from bot import get_setting
from utils.economy.manager import EconomyManager
from utils.daily.manager import DailyManager

economy = EconomyManager()

class DailyChestsView(miru.View):
    def __init__(self, dailyManager: DailyManager, user: hikari.User) -> None:
        super().__init__(timeout=None, autodefer=True)
        self.dailyManager = dailyManager
        self.user = user
        self.options = self.generate_options(dailyManager.streak)
        # print(self.options)
    
    @miru.text_select(
        custom_id='info_select',
        placeholder='Select a Treasure Chest',
        options=[
            miru.SelectOption(label='Old Chest', emoji='<:small_chest:1265769485441175562>', description='Worn and enigmatic, with tales of bygone days.', value='0'),
            miru.SelectOption(label='Standard Chest', emoji='<:medium_chest:1265769466109890693>', description='Unremarkable yet dependable.', value='1'),
            miru.SelectOption(label='Luxurious Chest', emoji='<:large_chest:1265769448095092777>', description='Lavish and extravagant, may promise grand rewards.', value='2'),
        ]
    )
    async def chests(self, ctx: miru.ViewContext, select: miru.TextSelect) -> None:
        amount = self.options[int(select.values[0])][0] * self.options[int(select.values[0])][1]
        economy.add_money(self.user.id, amount, True)

        match select.values[0]:
            case '0':
                chest = 'Old Chest'
                description = 'With a creaking sound, you gingerly open it. Inside, you find a modest sum of coins, their aged appearance hinting at the wisdom of the past. The Old Chest offers a reminder that even the simplest treasures hold value when viewed through the lens of history.'
                img = 'assets/img/emotes/small_chest.png'
            case '1':
                chest = 'Standard Chest'
                description = 'With a steady hand, you unlock it. Inside, you discover a sum of coins that neither beguiles nor overwhelms, leaving you with a sense of steady progression. The Standard Chest reaffirms the virtue of reliability in an unpredictable world.'
                img = 'assets/img/emotes/medium_chest.png'
            case '2':
                chest = 'Luxurious Chest'
                description = 'Tempted by the allure of immense wealth, you decide to open it. With a dramatic flourish, the chest reveals a dazzling array of coins. Yet, you sense the weight of responsibility that accompanies such wealth, a reminder that great riches come with equally great risks.'
                img = 'assets/img/emotes/large_chest.png'

        embed = hikari.Embed(title=f'You opened the {chest}', description=f'{description}\n\n> You earned 🪙 {amount}!\n> Your daily streak is now **{self.dailyManager.streak}**!\n\nCommand cooldown will reset at 12 AM EDT.', color=get_setting('general', 'embed_color'), timestamp=datetime.now().astimezone())
        embed.set_footer(text=f'Requested by {ctx.author.global_name}', icon=ctx.author.display_avatar_url)
        embed.set_thumbnail(img)
    
        await ctx.edit_response(embed, components=[])
        self.stop()
    
    def generate_coin_amount(self, streak: int) -> int:
        minCoins = 60 + (streak * 5)
        maxCoins = 120 + (streak * 10)
        return random.randint(minCoins, maxCoins)
    
    def generate_multiplier(self) -> int:
        multipliers = [1, 2, 3, 4]
        probabilities = [80, 10, 5, 1]
        return random.choices(multipliers, probabilities)[0]

    def generate_options(self, streak: int) -> list:
        options = []
        for i in range(3):
            amount = self.generate_coin_amount(streak)
            multiplier = self.generate_multiplier()
            options.append((amount, multiplier))
        return options
    
    async def view_check(self, ctx: ViewContext) -> bool:
        return ctx.user == self.user