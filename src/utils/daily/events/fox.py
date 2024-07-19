import hikari
import miru
import random

from datetime import datetime
from miru.context.view import ViewContext

from bot import get_setting
from utils.economy.manager import EconomyManager
from utils.daily.manager import DailyManager

economy = EconomyManager()

class DailyFoxView(miru.View):
    def __init__(self, dailyManager: DailyManager, user: hikari.User) -> None:
        super().__init__(timeout=None, autodefer=True)
        self.dailyManager = dailyManager
        self.user = user
        self.options = self.generate_options(dailyManager.streak)
        # print(self.options)
    
    @miru.text_select(
        custom_id='info_select',
        placeholder='Select an Option',
        options=[
            miru.SelectOption(label='PET THE GOD DAMN FOX', emoji='🫳', description='You simply must pet the fox, no questions asked.', value='0'),
            miru.SelectOption(label='Leave the Fox Alone', emoji='<:sleeping_fox:1143665534030848080>', description='Let the fox rest peacefully and continue with your day.', value='1'),
        ]
    )
    async def fox(self, ctx: miru.ViewContext, select: miru.TextSelect) -> None:
        amount = self.options[int(select.values[0])][0] * self.options[int(select.values[0])][1]
        economy.add_money(self.user.id, amount, True)

        embed = hikari.Embed(color=get_setting('general', 'embed_color'), timestamp=datetime.now().astimezone())
        match select.values[0]:
            case '0':
                embed.title = 'A Touch of Fate'
                embed.description = f'As you extend your hand to gently pet the curious red fox, you initiate a unique connection with the wild.\n\n> You earned 🪙 {amount}!\n> Your daily streak is now **{self.dailyManager.streak}**!\n\nCommand cooldown will reset at 12 AM EDT.'
            case '1':
                embed.title = "Respecting Nature's Rhythm"
                embed.description = f'As you stand there amidst the tranquil forest, you recognize the importance of allowing nature to unfold at its own pace. The fox, in its natural habitat, is a symbol of the untamed, unscripted beauty of the wilderness.\n\n> You earned 🪙 {amount}!\n> Your daily streak is now **{self.dailyManager.streak}**!\n\nCommand cooldown will reset at 12 AM EDT.'

        embed.set_footer(text=f'Requested by {ctx.author.global_name}', icon=ctx.author.display_avatar_url)
        embed.set_thumbnail('assets/img/general/dailies/fox.png')
    
        await ctx.edit_response(embed, components=[])
        self.stop()

    def generate_coin_amount(self, streak: int) -> int:
        minCoins = 80 + (streak * 10)
        maxCoins = 140 + (streak * 20)
        return random.randint(minCoins, maxCoins)
    
    def generate_multiplier(self) -> int:
        multipliers = [1, 2]
        probabilities = [75, 25]
        return random.choices(multipliers, probabilities)[0]

    def generate_options(self, streak: int) -> list:
        options = []
        for i in range(2):
            amount = self.generate_coin_amount(streak)
            multiplier = self.generate_multiplier()
            options.append((amount, multiplier))
        return options
    
    async def view_check(self, ctx: ViewContext) -> bool:
        return ctx.user == self.user