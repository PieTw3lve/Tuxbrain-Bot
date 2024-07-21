import hikari
import lightbulb
import miru

from miru.context import ViewContext
from miru.context.view import ViewContext
from miru.ext import nav
from PIL import Image

from bot import get_setting, verify_user, register_user
from utils.pokemon.inventory import NavPageInfo
from utils.economy.manager import EconomyManager
from utils.profile.inventory import Inventory
from utils.profile.card import Card

plugin = lightbulb.Plugin('Shop')
economy = EconomyManager()

class ProfileShopSelect(miru.SelectOption):
    def __init__(self, item: tuple) -> None:
        super().__init__(label=item[0], description='Click To View', value=item[1])

class NavShopSelectView(nav.NavTextSelect):
    def __init__(self, inventory:Inventory, items: list, maxItems: int, row: int) -> None:
        self.inventory = inventory
        self.items = items
        self.maxItems = maxItems
        self.options = [ProfileShopSelect(item) for item in self.get_items(0)]
        
        super().__init__(
            placeholder='Select a Item',
            options=self.options,
            row=row,
        )
    
    async def callback(self, ctx: ViewContext) -> None:
        if self.inventory.user.id != ctx.user.id:
            return
        
        profile = Card(plugin.bot.cache.get_member(ctx.get_guild(), ctx.user))
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
            
            embed = hikari.Embed(title=f'Do you want to purchase {name[0]} ({name[1]})?', description="This little maneuver's gonna cost you 51 years.", color=get_setting('general', 'embed_color'))
            image = await profile.draw_card(bg, card, nametag)
            embed.set_image(image)
            embed.set_footer(text='This action cannot be undone.')
            view = ProfileConfirmView(self.inventory, image, self.items, selected)
            message = await ctx.respond(embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)
            await view.start(message)
        else:
            embed = hikari.Embed(description='You already own this item!', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    async def before_page_change(self) -> None:
        self.options = [ProfileShopSelect(item) for item in self.get_items(self.view.current_page)]
    
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

class ProfileConfirmView(miru.View):
    def __init__(self, inventory: Inventory, image: bytes, items: list, selected: str) -> None:
        super().__init__(timeout=None, autodefer=True)
        self.inventory = inventory
        self.image = image
        self.items = items
        self.selected = selected
    
    @miru.button(label='Yes', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def yes(self, button: miru.Button, ctx: miru.ViewContext):
        currency, name, price = [item for item in self.items if item[1] == self.selected][0]
        
        if verify_user(ctx.user) == None: # if user has never been register
            register_user(ctx.user)

        if currency == 'coin' and economy.remove_money(ctx.user.id, price, True) == False: # checks if user has enough money
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        elif currency == 'tpass' and economy.remove_ticket(ctx.user.id, price) == False: # checks if user has enough tickets
            embed = hikari.Embed(description='You do not have enough tickets!', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        self.inventory.add_item((ctx.user.id, name.split("-")[0], name.split("-")[1], 0))

        embed = hikari.Embed(title='Thank you for your purchase!', color=get_setting('general', 'embed_success_color'))
        embed.set_image(self.image)
        await ctx.respond(embed)
    
    @miru.button(label='No', style=hikari.ButtonStyle.DANGER, row=1)
    async def no(self, button: miru.Button, ctx: miru.ViewContext): 
        await ctx.edit_response(components=[])
        self.stop()

class ChecksView(nav.NavigatorView):
    def __init__(self, inventory: Inventory, pages, buttons, timeout, autodefer: bool = True) -> None:
        super().__init__(pages=pages, items=buttons, timeout=timeout, autodefer=autodefer)
        self.inventory = inventory

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.inventory.user.id

@plugin.command
@lightbulb.command('shop', 'Customize your profile using coins or tux passes', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def customize(ctx: lightbulb.Context) -> None:
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
    buttons = [NavShopSelectView(inventory, items, 10, row=1), nav.PrevButton(emoji='⬅️', row=2), NavPageInfo(len(pages), row=2), nav.NextButton(emoji='➡️', row=2)]
    navigator = ChecksView(inventory, pages, buttons, timeout=None)
    client = ctx.bot.d.get('client')
    builder = await navigator.build_response_async(client=client, ephemeral=True)
    await builder.create_initial_response(ctx.interaction)
    client.start_view(navigator)

def load(bot):
    bot.add_plugin(plugin)