import hikari
import hikari.emojis
import miru

from miru.abc.item import InteractiveViewItem

from bot import get_setting
from utils.economy.manager import EconomyManager
from utils.economy.shop.fishing.confirm import FishingConfirmView
from utils.fishing.config_loader import FishingConfigLoader
from utils.fishing.inventory import Inventory

economy = EconomyManager()
baits = FishingConfigLoader().baits

class FishingShopView(miru.View):
    def __init__(self, user: hikari.User) -> None:
        super().__init__(timeout=None)
        self.items = [bait for bait in baits.values() if bait.price > 0]
        self.embed = embed = hikari.Embed(
            title='Welcome to the Fishing Shop!',
            description=(
                'Here, you can purchase bait to help reel in your next catch. Each type of fishing bait is unique, offering different **special effects**. '
                'While we only sell bait with basic effects, you can discover **rarer** bait while **salvaging** fish, so keep an eye out!\n\n'
                "On **Saturday** and **Sunday**, we offer a **30% discount** on all our bait, so plan accordingly to make the most of our offers!"
            ),
            color=get_setting('general', 'embed_color')
        )
        embed.add_field(name='Bait', value='\n'.join([f'{item.emoji} {item.name}' for item in self.items]), inline=True)
        embed.add_field(name='Amount', value='\n'.join(['5x'] * len(self.items)), inline=True)
        embed.add_field(name='Price', value='\n'.join([f'🪙 {round(item.current_price() * 5)}' for item in self.items]), inline=True)
        embed.set_thumbnail(hikari.emojis.Emoji.parse('🎣').url)
        self.menu = self.add_item(miru.TextSelect(
            custom_id='bait_select',
            placeholder='Select a Bait',
            options=[
                miru.SelectOption(
                    label=f'{item.name} (5x)',
                    emoji=item.emoji,
                    description=item.tooltip,
                    value=item.id
                ) for item in self.items
            ]
        ))
        self.author = user

    async def _handle_callback(self, item: InteractiveViewItem, ctx: miru.ViewContext) -> None:
        bait = baits[ctx.interaction.values[0]]
        price = round(bait.current_price() * 5)
        
        view = FishingConfirmView(ctx.user, bait, 5)
        await ctx.respond(view.embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)
        client = ctx.client
        client.start_view(view)
        await view.wait()
        
        match view.response:
            case 'confirm':
                if economy.remove_money(ctx.user.id, price, True) is False:
                    embed = hikari.Embed(
                        title='Insufficient Funds',
                        description='You do not have enough money to purchase this bait.',
                        color=get_setting('general', 'embed_error_color')
                    )
                    return await ctx.respond(embed=embed, flags=hikari.MessageFlag.EPHEMERAL)
                else:
                    inventory = Inventory(ctx.user)
                    inventory.update_bait(bait, inventory.get_bait_amount(bait) + 5)
                    embed = hikari.Embed(
                        title='Purchase Successful',
                        description=f'You have successfully purchased **{bait.emoji} {bait.name} (5x)** for 🪙 {price}.',
                        color=get_setting('general', 'embed_success_color')
                    )
                    return await ctx.respond(embed=embed)

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.author.id