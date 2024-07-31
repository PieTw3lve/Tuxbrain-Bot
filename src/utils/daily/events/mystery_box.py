import hikari
import miru
import random

from datetime import datetime
from miru.context.view import ViewContext

from bot import get_setting, verify_user, register_user
from utils.economy.manager import EconomyManager
from utils.daily.manager import DailyManager

economy = EconomyManager()

class DailyMysteryBoxView(miru.View):
    def __init__(self, dailyManager: DailyManager, user: hikari.User) -> None:
        super().__init__(timeout=None, autodefer=True)
        self.dailyManager = dailyManager
        self.user = user
        self.options = self.generate_options(dailyManager.streak)
        # print(self.options)
    
    @miru.user_select(placeholder='Select a User')
    async def get_users(self, ctx: miru.ViewContext, select: miru.UserSelect) -> None:
        user = select.values[0]
        if user.is_bot:
            embed = hikari.Embed(description="Bots don't have the rights to earn money!", color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        elif user.id == ctx.user.id:
            amount = round(self.options[1][0] * self.options[1][1])
            economy.add_money(self.user.id, amount, True)

            embed = hikari.Embed(title=f'A Solitary Journey into the Unknown', description=f'With a resolute spirit, you decide to open the enigmatic mystery box solely for yourself. As you carefully lift the lid, a sense of adventure courses through you. What awaits within is exclusively yours, a treasure that reflects your individual journey.\n\n> You earned 🪙 {amount}!\n> Your daily streak is now **{self.dailyManager.streak}**!\n\nCommand cooldown will reset at 12 AM EDT.', color=get_setting('general', 'embed_color'), timestamp=datetime.now().astimezone())
            embed.set_thumbnail('assets/img/general/daily/question_mark.png')
            embed.set_footer(text=f'Requested by {ctx.author.global_name}', icon=ctx.author.display_avatar_url)
        
            await ctx.edit_response(embed, components=[])
            self.stop()
        else:
            if verify_user(user) == None: # if user has never been register
                register_user(user)
            
            amount = self.options[0][0] * self.options[0][1]
            economy.add_money(self.user.id, amount, True)
            economy.add_money(user.id, amount, True)
            
            embed = hikari.Embed(title=f'A Bond Forged Through Sharing', description=f'As you choose to share the enigmatic mystery box with {user.global_name}, a sense of anticipation fills the air. Gently, you pass the box to {user.global_name}, and together, you both open it.\n\n> You and <@{user.id}> earned 🪙 {amount}!\n> Your daily streak is now **{self.dailyManager.streak}**!\n\nCommand cooldown will reset at 12 AM EST.', color=get_setting('general', 'embed_color'), timestamp=datetime.now().astimezone())
            embed.set_thumbnail('assets/img/general/daily/question_mark.png')
            embed.set_footer(text=f'Requested by {ctx.author.global_name}', icon=ctx.author.display_avatar_url)
        
            await ctx.edit_response(embed, components=[])
            self.stop()
    
    def generate_coin_amount(self, streak: int) -> int:
        minCoins = 60 + (streak * 5)
        maxCoins = 120 + (streak * 10)
        return random.randint(minCoins, maxCoins)
    
    def generate_multiplier(self) -> int:
        multipliers = [0.25, 0.5, 1, 2]
        probabilities = [10, 80, 20, 5]
        return random.choices(multipliers, probabilities)[0]

    def generate_options(self, streak: int) -> list:
        options = []
        for i in range(2):
            if i % 2 == 0:
                amount = self.generate_coin_amount(streak)
                multiplier = 1
                options.append((amount, multiplier))
            else:
                amount = self.generate_coin_amount(streak)
                multiplier = self.generate_multiplier()
                options.append((amount, multiplier))
        return options

    async def view_check(self, ctx: ViewContext) -> bool:
        return ctx.user == self.user