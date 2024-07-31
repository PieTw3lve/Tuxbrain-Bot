import hikari
import lightbulb
import miru

from miru.ext import nav

from bot import get_setting
from utils.economy.shop.fishing.view import FishingShopView
from utils.economy.shop.profile.navigator import NavShopSelectView
from utils.economy.shop.profile.checks import ChecksView
from utils.general.navigator import NavPageInfo
from utils.profile.inventory import Inventory

plugin = lightbulb.Plugin('Shop')

class ShopSelectView(miru.View):
    def __init__(self, user: hikari.User) -> None:
        super().__init__(timeout=None)
        self.author = user
        self.option = None
    
    @miru.text_select(
        custom_id='shop_select',
        placeholder='Select a Shop',
        options=[
            miru.SelectOption(label='Profile Shop', emoji='🎨', description='Personalize your profile with a wide range of options.', value='profile'),
            miru.SelectOption(label='Fishing Shop', emoji='🎣', description='Find the perfect bait to reel in your next big catch.', value='fishing'),
        ]
    )
    async def shop_select(self, ctx: miru.ViewContext, select: miru.TextSelect) -> None:
        self.option = select.values[0]
        self.stop()

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.author.id

@plugin.command
@lightbulb.command('shop', 'Spend your hard-earned coins and tickets on a variety of items!', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def customize(ctx: lightbulb.Context) -> None:
    view = ShopSelectView(ctx.author)
    embed = hikari.Embed(
        title=f'Select a Shop',
        description='Spend your hard-earned coins and tickets on a variety of items!',
        color=get_setting('general', 'embed_color')
    )
    
    await ctx.respond(embed, components=view.build())
    client = ctx.bot.d.get('client')
    client.start_view(view)
    await view.wait()

    # await ctx.delete_last_response()

    match view.option:
        case 'profile':
            inventory = Inventory(ctx.member)
            profiles = get_setting('profile')
            coinItems = []
            tpassItems = []

            # Iterate through 'coin' and add tuples to result
            for item, price in profiles['coin'].items():
                coinItems.append(('coin', item, price))
            coinItems.sort(key=lambda x: x[2], reverse=True)

            # Iterate through 'tpass' and add tuples to result
            for item, price in profiles['tpass'].items():
                tpassItems.append(('tpass', item, price))
            tpassItems.sort(key=lambda x: x[2], reverse=True)

            items =  coinItems + tpassItems

            pages = inventory.get_pages(items, 10)
            buttons = [NavShopSelectView(ctx, inventory, items, 10, row=1), nav.PrevButton(emoji='⬅️', row=2), NavPageInfo(len(pages), row=2), nav.NextButton(emoji='➡️', row=2)]
            navigator = ChecksView(inventory, pages, buttons, timeout=None)
            await ctx.edit_last_response(embed=pages[0], components=navigator.build())
            client.start_view(navigator)
        case 'fishing':
            view = FishingShopView(ctx.author)
            await ctx.edit_last_response(embed=view.embed, components=view.build())
            client.start_view(view)

def load(bot):
    bot.add_plugin(plugin)