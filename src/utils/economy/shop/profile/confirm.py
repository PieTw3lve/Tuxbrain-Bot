import hikari
import miru

from bot import get_setting, register_user, verify_user
from utils.economy.manager import EconomyManager
from utils.profile.inventory import Inventory

economy = EconomyManager()

class ProfileConfirmView(miru.View):
    def __init__(self, inventory: Inventory, image: bytes, items: list, selected: str) -> None:
        super().__init__(timeout=None, autodefer=True)
        self.inventory = inventory
        self.image = image
        self.items = items
        self.selected = selected
    
    @miru.button(label='Yes', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def yes(self, ctx: miru.ViewContext, button: miru.Button):
        currency, name, price = [item for item in self.items if item[1] == self.selected][0]
        
        if verify_user(ctx.user) == None: # if user has never been register
            register_user(ctx.user)

        if currency == 'coin' and economy.remove_money(ctx.user.id, price, True) == False: # checks if user has enough money
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        elif currency == 'tpass' and economy.remove_ticket(ctx.user.id, price) == False: # checks if user has enough tickets
            embed = hikari.Embed(description='You do not have enough tickets!', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        self.inventory.add_item((ctx.user.id, name.split('-')[0], name.split('-')[1], 0))

        embed = hikari.Embed(title='Thank you for your purchase!', color=get_setting('general', 'embed_success_color'))
        embed.set_image(self.image)
        await ctx.respond(embed)
    
    @miru.button(label='No', style=hikari.ButtonStyle.DANGER, row=1)
    async def no(self, ctx: miru.ViewContext, button: miru.Button): 
        await ctx.edit_response(components=[])
        self.stop()