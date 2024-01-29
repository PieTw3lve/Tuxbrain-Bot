import hikari
import lightbulb
import miru
import sqlite3

from miru.ext import nav
from miru.context.view import ViewContext

from bot import get_setting
from utils.economy.manager import EconomyManager

economy = EconomyManager()

class Inventory:
    def __init__(self, ctx: lightbulb.Context, user: hikari.User):
        self.db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        self.cursor = self.db.cursor()
        self.user = user
        self.ctx = ctx
        self.max = get_setting('pokemon', 'pokemon_max_capacity')

    def show_inventory(self, items_per_page):
        inventory = self.get_inventory()

        if not inventory:
            embed = hikari.Embed(title=f"{self.user.global_name}'s Inventory", description=f'No cards or packs found!', color=get_setting('settings', 'embed_color'))
            return [embed]
        else:
            items, cards = inventory
        
        pages = []
        for i in range(0, len(items), items_per_page):
            embed = hikari.Embed(title=f"{self.user.global_name}'s Inventory", description=f'Capacity: `{self.get_inventory_capacity()}/{self.max}`', color=get_setting('settings', 'embed_color'))
            # embed.set_thumbnail('assets/img/pokemon/inventory_icon.png')
            end = i + items_per_page
            for pack in items[i:end]:
                id, userID, date, name = pack
                if len(embed.fields) == 0:
                    embed.add_field(name='Pack Type', value=f'• {name} Pack', inline=True)
                    embed.add_field(name='Pack ID', value=f'{id}', inline=True)
                else:
                    embed.edit_field(0, embed.fields[0].name, f'{embed.fields[0].value}\n• {name} Pack')
                    embed.edit_field(1, embed.fields[1].name, f'{embed.fields[1].value}\n{id}')
            pages.append(embed)
        for i in range(0, len(cards), items_per_page):
            embed = hikari.Embed(title=f"{self.user.global_name}'s Inventory", description=f'Capacity: `{self.get_inventory_capacity()}/{self.max}`', color=get_setting('settings', 'embed_color'))
            # embed.set_thumbnail('assets/img/pokemon/inventory_icon.png')
            end = i + items_per_page
            for card in cards[i:end]:
                id, userID, date, name, pokemonId, rarity, shiny, favorite = card
                emoji_star = '⭐' if not shiny else '🌟'
                name_symbol = '' if not shiny else '**'
                favorite_symbol = '' if not favorite else '<:favorite_icon:1074056642368377023>'
                rarity_emoji = emoji_star * int(rarity)
                if len(embed.fields) == 0:
                    embed.add_field(name='Pokémon Name', value=f'• {name_symbol}{name}{name_symbol} {favorite_symbol}', inline=True)
                    embed.add_field(name='Card Quality', value=f'{rarity_emoji}', inline=True)
                    embed.add_field(name='Card ID', value=f'{id}', inline=True)
                else:
                    embed.edit_field(0, embed.fields[0].name, f'{embed.fields[0].value}\n• {name_symbol}{name}{name_symbol} {favorite_symbol}')
                    embed.edit_field(1, embed.fields[1].name, f'{embed.fields[1].value}\n{rarity_emoji}')
                    embed.edit_field(2, embed.fields[2].name, f'{embed.fields[2].value}\n{id}')
            pages.append(embed)

        return pages

    def get_inventory(self):
        self.cursor.execute("SELECT * FROM pokemon WHERE user_id=? AND name NOT IN (?, ?) ORDER BY name ASC, shiny DESC, rarity DESC, favorite DESC, date ASC;", (self.user.id, 'Standard', 'Premium'))
        cards = self.cursor.fetchall()
        self.cursor.execute("SELECT id, user_id, date, name FROM pokemon WHERE user_id=? AND name IN (?, ?) ORDER BY name ASC, date ASC;", (self.user.id, 'Standard', 'Premium'))
        items = self.cursor.fetchall()

        if not cards and not items:
            return None
        
        return items, cards
    
    def get_item(self, id):
        query = "SELECT id, user_id, date, name FROM pokemon WHERE id = ? AND user_id = ? AND name IN (?, ?)"
        self.cursor.execute(query, (id, self.user.id, 'Standard', 'Premium'))
        pack = self.cursor.fetchone()
        
        if pack:
            return 'Pack', pack

        query = "SELECT * FROM pokemon WHERE id = ? AND user_id = ? AND name NOT IN (?, ?)"
        self.cursor.execute(query, (id, self.user.id, 'Standard', 'Premium'))
        card = self.cursor.fetchone()
        
        if card:
            return 'Card', card

        return None

    def get_dupe_cards(self, s: bool, all: bool):
        cards = self.get_inventory()[1]
        
        # Removes all unique cards that are favorited
        if not all:
            uniqueCards = {}
        
            for card in cards:
                cardId = card[0]
                userId = card[1]
                date = card[2]
                name = card[3]
                pokemonId = card[4]
                rarity = card[5]
                shiny = card[6]
                favorite = card[7]
                
                cardKey = (pokemonId, rarity, shiny, favorite)

                if cardKey not in uniqueCards:
                    uniqueCards[cardKey] = (cardId, userId, date, name, pokemonId, rarity, shiny, favorite)
                else:
                    existing_date = uniqueCards[cardKey][2]
                    if date < existing_date:
                        uniqueCards[cardKey] = (cardId, userId, date, name, pokemonId, rarity, shiny, favorite)
            
            for card in list(uniqueCards.values()):
                cards.remove(card)

        # Removes all cards that are favorited
        cards = [card for card in cards if card[-1] == 0]

        # Removes all cards that are shiny
        cards = [card for card in cards if card[-2] == 0] if not s else cards
        
        return cards
    
    def get_inventory_capacity(self):
        items, cards = self.get_inventory()
        total = len(items) + len(cards)
        return total

    async def sell(self, cards: list) -> None:
        value = 0
        for card in cards:
            cardID = card[0]
            shiny = card[6]
            favorite = card[7]
            if favorite or not self.get_item(cardID):
                embed = hikari.Embed(title='Sell Error', description='At least one card is favorited or does not exist.', color=get_setting('settings', 'embed_error_color'))
                embed.set_thumbnail('assets/img/pokemon/convert_icon.png')
                await self.ctx.edit_last_response(embed, components=[])
                return
            value += 40 if shiny else 20
        for card in cards:
            try:
                self.db.execute('DELETE FROM pokemon WHERE id=?', (card[0],))
                self.db.commit()
            except sqlite3.Error as e:
                self.db.rollback()
                print("Error deleting item from the database:", e)
        self.db.commit()
        economy.add_money(self.user.id, value, True)

        embed = hikari.Embed(title='Success', description=f'You sold {len(cards)} cards for 🪙 {value}!', color=get_setting('settings', 'embed_success_color'))
        embed.set_thumbnail('assets/img/pokemon/convert_icon.png')
        # embed.set_footer('Your balance has been updated.')
        await self.ctx.edit_last_response(embed, components=[])

    def __del__(self):
        self.db.close()

class SellView(miru.View):
    def __init__(self, embed: hikari.Embed, inventory: Inventory) -> None:
        super().__init__(timeout=None, autodefer=True)
        self.embed = embed
        self.inventory = inventory
    
    @miru.text_select(
        placeholder='Select A Sell Option',
        options=[
            miru.SelectOption(label='Sell Duplicates (Exclude Shinies)', value='1'),
            miru.SelectOption(label='Sell Duplicates (Include Shinies)', value='2'),
            miru.SelectOption(label='Sell All (Exclude Shinies)', value='3'),
            miru.SelectOption(label='Sell All (Include Shinies)', value='4'),
        ],
        row=1
    )
    async def sell_option(self, select: miru.TextSelect, ctx: miru.Context):
        option = select.values[0]

        match option:
            case '1':
                cards = self.inventory.get_dupe_cards(False, False)
            case '2':
                cards = self.inventory.get_dupe_cards(True, False)
            case '3':
                cards = self.inventory.get_dupe_cards(False, True)
            case '4':
                cards = self.inventory.get_dupe_cards(True, True)
        
        view = PromptView()
        self.embed.title = 'Are you sure?'
        self.embed.color = get_setting('settings', 'embed_error_color')
        self.embed.set_footer('This action is irreversible!')
        message = await ctx.edit_response(self.embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)

        await view.start(message)
        await view.wait()
        
        if view.answer:
            await self.inventory.sell(cards)
        else:
            self.embed.title = 'Selling proccess has been cancelled.'
            self.embed.description = 'No cards has been sold.'
            self.embed.set_footer(None)
            await ctx.edit_response(self.embed, components=[], flags=hikari.MessageFlag.EPHEMERAL)
    
    async def view_check(self, ctx: ViewContext) -> bool:
        return self.inventory.get_inventory() != None
    
class ChecksView(nav.NavigatorView):
    def __init__(self, user: hikari.User, pages, buttons, timeout, autodefer: bool = True) -> None:
        super().__init__(pages=pages, buttons=buttons, timeout=timeout, autodefer=autodefer)
        self.user = user

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.user.id
    
class NavPageInfo(nav.NavButton):
    def __init__(self, pages: int, row: int):
        super().__init__(label="Page: 1", style=hikari.ButtonStyle.SECONDARY, disabled=True, row=row)
        self.pages = pages

    async def callback(self, ctx: miru.ViewContext) -> None:
        return

    async def before_page_change(self) -> None:
        self.label = f'Page: {self.view.current_page+1}/{self.pages}'

class PromptView(miru.View):
    def __init__(self) -> None:
        super().__init__(timeout=None, autodefer=True)
        self.answer = False
    
    @miru.button(label='Confirm', style=hikari.ButtonStyle.SUCCESS)
    async def confirm(self, button: miru.Button, ctx: miru.Context) -> None:
        self.answer = True
        self.stop()
    
    @miru.button(label='Cancel', style=hikari.ButtonStyle.DANGER)
    async def cancel(self, button: miru.Button, ctx: miru.Context) -> None:
        self.stop()
