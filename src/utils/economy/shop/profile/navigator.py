import hikari
import lightbulb

from miru import ViewContext
from miru.ext import nav
from PIL import Image

from bot import get_setting
from utils.economy.shop.profile.confirm import ProfileConfirmView
from utils.economy.shop.profile.option import ProfileOptionSelect
from utils.profile.card import Card
from utils.profile.inventory import Inventory


class NavShopSelectView(nav.NavTextSelect):
    def __init__(self, ctx: lightbulb.Context, inventory:Inventory, items: list, maxItems: int, row: int) -> None:
        self.inventory = inventory
        self.items = items
        self.maxItems = maxItems
        self.options = [ProfileOptionSelect(item) for item in self.get_items(0)]
        self.ctx = ctx
        
        super().__init__(
            placeholder='Select a Item',
            options=self.options,
            row=row,
        )
    
    async def callback(self, ctx: ViewContext) -> None:
        if self.inventory.user.id != ctx.user.id:
            return
        
        profile = Card(ctx.client.cache.get_member(ctx.get_guild(), ctx.user), self.ctx)
        selected = self.values[0]
        name = selected.replace('_', ' ').title().split('-')
        
        if self.inventory.get_profile_item(selected.split('-')) == False:
            bg, card, nametag = self.inventory.get_active_customs()
            bg = Image.open(f'assets/img/general/profile/banner/{bg}.png').convert('RGBA')
            card = Image.open(f'assets/img/general/profile/base/{card}.png').convert('RGBA')
            nametag = Image.open(f'assets/img/general/profile/nametag/{nametag}.png').convert('RGBA')
            
            match selected.split('-')[1]:
                case 'banner':
                    bg = Image.open(f'assets/img/general/profile/banner/{selected}.png').convert('RGBA')
                case 'base':
                    card = Image.open(f'assets/img/general/profile/base/{selected}.png').convert('RGBA')
                case 'nametag':
                    nametag = Image.open(f'assets/img/general/profile/nametag/{selected}.png').convert('RGBA')
            
            embed = hikari.Embed(title=f'Do you want to purchase {name[0]} ({name[1]})?', color=get_setting('general', 'embed_color'))
            image = await profile.draw_card(bg, card, nametag)
            embed.set_image(image)
            embed.set_footer(text='This action cannot be undone.')
            view = ProfileConfirmView(self.inventory, image, self.items, selected)
            await ctx.respond(embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)
            client = ctx.client
            client.start_view(view)
        else:
            embed = hikari.Embed(description='You already own this item!', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    async def before_page_change(self) -> None:
        self.options = [ProfileOptionSelect(item) for item in self.get_items(self.view.current_page)]
    
    def get_items(self, index: int):
        pages = []
        for i in range(0, len(self.items), self.maxItems):
            end = i + self.maxItems
            page = []
            for option in self.items[i:end]:
                currency, name, price = option
                strName = str(name).replace('_', ' ').capitalize().split('-')
                strName = f'{strName[0].title()} ({strName[1]})'
                page.append((strName, name))
            pages.append(page)
        return pages[index]