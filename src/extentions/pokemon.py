import hikari
import lightbulb
import miru
import random
import sqlite3
import requests
import uuid
import datetime
import pytz

from bot import get_setting, verify_user
from extentions.economy import add_money, remove_money, remove_ticket
from miru.ext import nav
from miru.context.view import ViewContext
from typing import Optional

plugin = lightbulb.Plugin('Pokemon')
timezone = pytz.timezone("America/New_York")

class PokemonPack:
    def __init__(self, user: hikari.User, pack_id, pack_type):
        self.user = user
        self.pack_id = pack_id
        self.pack_type = pack_type

class PokemonCard:
    def __init__(self, user: hikari.User, card_id, date, name, pokemon_id, rarity, shiny=False):
        self.user = user
        self.card_id = card_id
        self.name = name
        self.date = date
        self.pokemon_id = pokemon_id
        self.rarity = rarity
        self.shiny = shiny

    def display(self, pages: list) -> list:
        if self.shiny:
            rarity_symbol = '🌟'
        else:
            rarity_symbol = '⭐'
        
        embed = hikari.Embed(title=f'{self.name} Card' if not self.shiny else f'Shiny {self.name} Card', color=get_setting('embed_color'))
        embed.set_image(f'https://img.pokemondb.net/sprites/home/normal/{self.name.lower()}.png' if not self.shiny else f'https://img.pokemondb.net/sprites/home/shiny/{self.name.lower()}.png')
        # embed.set_image(f'https://raw.githubusercontent.com/harshit23897/Pokemon-Sprites/master/assets/imagesHQ/{"{:03d}".format(pokemon_id)}.png') # If you want 2d sprites. This does not support shiny sprites.
        embed.add_field(name='Pokémon Name', value=self.name, inline=True)
        embed.add_field(name='Card Quality', value=" ".join([rarity_symbol for i in range(self.rarity)]), inline=True)
        embed.add_field(name='Card ID', value=f'`{self.card_id}`', inline=False)
        embed.set_footer('Type `/inventory` to view your cards and packs.')
        
        pages.append(embed)
        return pages
    
    def display_overview(self, embed: hikari.Embed) -> hikari.Embed:
        if self.shiny:
            name_symbol = '**'
            rarity_symbol = '🌟'
        else:
            name_symbol = ''
            rarity_symbol = '⭐'

        if len(embed.fields) == 0:
            embed.add_field(name='Pokémon Name', value=f'• {name_symbol}{self.name}{name_symbol}', inline=True)
            embed.add_field(name='Card Quality', value=" ".join([rarity_symbol for i in range(self.rarity)]), inline=True)
            embed.add_field(name='Card ID', value=f'{self.card_id}', inline=True)
        else:
            embed.edit_field(0, embed.fields[0].name, f'{embed.fields[0].value}\n• {name_symbol}{self.name}{name_symbol}')
            embed.edit_field(1, embed.fields[1].name, f'{embed.fields[1].value}\n{" ".join([rarity_symbol for i in range(self.rarity)])}')
            embed.edit_field(2, embed.fields[2].name, f'{embed.fields[2].value}\n{self.card_id}')
        
        return embed

class StandardPokemonCardPack:
    def __init__(self, user: hikari.User, ctx: miru.Context):
        self.user = user
        self.ctx = ctx
    
    async def buy(self):
        self.db = sqlite3.connect(get_setting('database_data_dir'))
        self.cursor = self.db.cursor()
        
        pack_id = str(uuid.uuid4())
        current_date = datetime.datetime.now(timezone)
        date = current_date.strftime('%m/%d/%Y')
        pack_type = 'Standard'

        self.cursor.execute("INSERT INTO items (id, user_id, date, type) VALUES (?,?,?,?)", (pack_id, self.user.id, date, pack_type))
        self.db.commit()

        embed = hikari.Embed(title='Pokémon Booster Pack Shop', description=f'Thank you for your purchase <@{self.user.id}>!\nPack ID: `{pack_id}`', color=get_setting('embed_success_color'))
        embed.set_thumbnail('assets/img/pokemon/shop_icon.png')
        await self.ctx.respond(embed, delete_after=30)

    async def open(self, pack_id):
        self.cards = []
        
        self.db = sqlite3.connect(get_setting('database_data_dir'))
        self.cursor = self.db.cursor()
        
        pokeapi_url = "https://pokeapi.co/api/v2/pokemon?limit=251"
        response = requests.get(pokeapi_url)
        pokemon_list = response.json()["results"]
        
        for i in range(7):
            pokemon = random.choice(pokemon_list)
            pokemon_response = requests.get(pokemon["url"])
            pokemon_data = pokemon_response.json()
            rand = random.random()
            rarity = 0
            shiny = False
            favorite = False
            if rand <= 0.01: # 1% chance
                rand = random.random()
                shiny = True
                rarity = 1
                if rand <= 0.1: # 10% (0.1%) chance 
                    rarity = 2
                if rand <= 0.01: # 1% (0.01%) chance 
                    rarity = 3
            else:
                rand = random.random()
                rarity = 1
                if random.random() <= 0.3: # 30% chance
                    rarity = 2
                if random.random() <= 0.1: # 10% chance
                    rarity = 3
                if random.random() <= 0.005: # 0.5% chance
                    rarity = 4
                if random.random() <= 0.001: # 0.1% chance
                    rarity = 5
            card_id = str(uuid.uuid4())
            current_date = datetime.datetime.now(timezone)
            date = current_date.strftime('%m/%d/%Y')
            self.cards.append(PokemonCard(self.user, card_id, date, pokemon_data["name"].capitalize(), pokemon_data["id"], rarity, shiny))
            self.cursor.execute("INSERT INTO cards (id, user_id, date, name, pokemon_id, rarity, shiny, favorite) VALUES (?,?,?,?,?,?,?,?)", (card_id, self.user.id, date, pokemon_data["name"].capitalize(), pokemon_data["id"], rarity, int(shiny), int(favorite)))
        
        self.db.execute('DELETE FROM items WHERE id=?', (pack_id,))
        self.db.commit()

        embed = hikari.Embed(title=f'Standard Booster Pack Overview', color=get_setting('embed_color'))
        embed.set_footer('Type `/inventory` to view your cards and packs.')

        pages = []
        for card in self.cards:
            pages = card.display(pages)
            embed = card.display_overview(embed)
        pages.append(embed)
        
        buttons = [nav.PrevButton(emoji='⬅️'), NavPageInfo(len(pages)), nav.NextButton(emoji='➡️'), nav.LastButton()]
        navigator = nav.NavigatorView(pages=pages, buttons=buttons, timeout=None)

        await navigator.send(self.ctx.interaction)

    def __del__(self):
        self.db.close()

class PremiumPokemonCardPack:
    def __init__(self, user: hikari.User, ctx: miru.Context):
        self.user = user
        self.ctx = ctx
    
    async def buy(self):
        self.db = sqlite3.connect(get_setting('database_data_dir'))
        self.cursor = self.db.cursor()
        
        pack_id = str(uuid.uuid4())
        current_date = datetime.datetime.now(timezone)
        date = current_date.strftime('%m/%d/%Y')
        pack_type = 'Premium'

        self.cursor.execute("INSERT INTO items (id, user_id, date, type) VALUES (?,?,?,?)", (pack_id, self.user.id, date, pack_type))
        self.db.commit()

        embed = hikari.Embed(title='Pokémon Booster Pack Shop', description=f'Thank you for your purchase <@{self.user.id}>!\nPack ID: `{pack_id}`', color=get_setting('embed_success_color'))
        embed.set_thumbnail('assets/img/pokemon/shop_icon.png')
        embed.set_footer('Type `/inventory` to see your packs!')
        await self.ctx.respond(embed, delete_after=30)

    async def open(self, pack_id):
        self.cards = []
        
        self.db = sqlite3.connect(get_setting('database_data_dir'))
        self.cursor = self.db.cursor()
        
        pokeapi_url = "https://pokeapi.co/api/v2/pokemon?limit=251"
        response = requests.get(pokeapi_url)
        pokemon_list = response.json()["results"]
        
        for i in range(7):
            pokemon = random.choice(pokemon_list)
            pokemon_response = requests.get(pokemon["url"])
            pokemon_data = pokemon_response.json()
            rand = random.random()
            rarity = 0
            shiny = False
            favorite = False
            if rand <= 0.03: # 3% chance
                rand = random.random()
                shiny = True
                rarity = 1
                if rand <= 0.3: # 30% (0.9%) chance 
                    rarity = 2
                if rand <= 0.03: # 3% (0.09%) chance 
                    rarity = 3
            else:
                rand = random.random()
                rarity = 1
                if rand <= 0.9: # 90% chance
                    rarity = 2
                if rand <= 0.3: # 30% chance
                    rarity = 3
                if rand <= 0.015: # 0.15% chance
                    rarity = 4
                if rand <= 0.003: # 0.3% chance
                    rarity = 5
            card_id = str(uuid.uuid4())
            current_date = datetime.datetime.now(timezone)
            date = current_date.strftime('%m/%d/%Y')
            self.cards.append(PokemonCard(self.user, card_id, date, pokemon_data["name"].capitalize(), pokemon_data["id"], rarity, shiny))
            self.cursor.execute("INSERT INTO cards (id, user_id, date, name, pokemon_id, rarity, shiny, favorite) VALUES (?,?,?,?,?,?,?,?)", (card_id, self.user.id, date, pokemon_data["name"].capitalize(), pokemon_data["id"], rarity, int(shiny), int(favorite)))
        
        self.db.execute('DELETE FROM items WHERE id=?', (pack_id,))
        self.db.commit()

        embed = hikari.Embed(title=f'Premium Booster Pack Overview', color=get_setting('embed_color'))
        embed.set_footer('Type `/inventory` to view your cards and packs.')

        pages = []
        for card in self.cards:
            pages = card.display(pages)
            embed = card.display_overview(embed)
        pages.append(embed)
        
        buttons = [nav.PrevButton(emoji='⬅️'), NavPageInfo(len(pages)), nav.NextButton(emoji='➡️'), nav.LastButton()]
        navigator = nav.NavigatorView(pages=pages, buttons=buttons, timeout=None)

        await navigator.send(self.ctx.interaction)

    def __del__(self):
        self.db.close()

## Packs Shop Commands ##

class PackShop(miru.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
    
    @miru.button(label='Standard Pack', emoji='<:standard_booster_pack:1073771426324156428>', style=hikari.ButtonStyle.PRIMARY, custom_id='standard_pack_button')
    async def standard(self, button: miru.Button, ctx: miru.Context) -> None:
        if verify_user(ctx.user) == None: # if user has never been register
            embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif remove_money(ctx.user.id, 200, True) == False: # checks if user has enough money
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return

        pack = StandardPokemonCardPack(ctx.user, ctx)
        await pack.buy()
    
    @miru.button(label='Premium Pack', emoji='<:premium_booster_pack:1073771425095237662>', style=hikari.ButtonStyle.PRIMARY, custom_id='premium_pack_button')
    async def premium(self, button: miru.Button, ctx: miru.Context) -> None:
        if verify_user(ctx.user) == None: # if user has never been register
            embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        if remove_ticket(ctx.user.id, 1) == False: # checks if user has enough tickets
            embed = hikari.Embed(description='You do not have enough tickets!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        pack = PremiumPokemonCardPack(ctx.user, ctx)
        await pack.buy()

    @miru.button(label='What are Booster Packs?', emoji='❔', style=hikari.ButtonStyle.SECONDARY, custom_id='card_pack_info')
    async def info(self, button: miru.Button, ctx: miru.Context) -> None:
        embed = hikari.Embed(title='What are Booster Packs?', description="Pokémon Booster Packs are packs of 7 randomly selected Pokémon cards, up to Gen 2, that enhance your Pokémon card collection. They include rare cards ranging from 1-5 ⭐, with a chance of finding a shiny Pokémon. You can purchase the standard booster packs using PokéCoins, and premium booster packs require 1 🎟️. Collect and trade cards with other players to build an impressive collection of Gen 2 and earlier Pokémon cards. Perfect for beginners and seasoned collectors alike.", color=get_setting('embed_color'))
        embed.set_thumbnail('assets/img/pokemon/shop_icon.png')
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@plugin.command
@lightbulb.command('shop', 'Open the PokéShop menu.')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def shop(ctx: lightbulb.Context) -> None:
    embed = hikari.Embed(title='Welcome to the PokéShop!', description='Get your hands on the newest Pokémon cards at the Pokémon Booster Pack Shop! Simply choose from one of the two options below to start building your collection today. \n\nA standard booster pack costs 🪙 200, while the premium booster pack, which offers a **3x boost** on the chance of getting rare quality cards, can be yours for just 1 🎟️.', color=get_setting('embed_color'))
    embed.set_thumbnail('assets/img/pokemon/shop_icon.png')

    view = PackShop()
    message = await ctx.respond(embed, components=view.build())

    await view.start(message)

## Packs Inventory View Command ##

class Inventory:
    def __init__(self, ctx: lightbulb.Context, user: hikari.User):
        self.db = sqlite3.connect(get_setting('database_data_dir'))
        self.cursor = self.db.cursor()
        self.user = user
        self.ctx = ctx

    def show_inventory(self, items_per_page):
        inventory = self.get_inventory()

        if not inventory:
            embed = hikari.Embed(title=f"{self.user.username}'s Inventory", description=f'No cards or packs found!', color=get_setting('embed_color'))
            return [embed]
        else:
            items, cards = inventory
        
        pages = []
        for i in range(0, len(items), items_per_page):
            embed = hikari.Embed(title=f"{self.user.username}'s Inventory", color=get_setting('embed_color'))
            # embed.set_thumbnail('assets/img/pokemon/inventory_icon.png')
            end = i + items_per_page
            for pack in items[i:end]:
                id, user_id, date, name = pack
                if len(embed.fields) == 0:
                    embed.add_field(name='Pack Type', value=f'• {name} Pack', inline=True)
                    embed.add_field(name='Pack ID', value=f'{id}', inline=True)
                else:
                    embed.edit_field(0, embed.fields[0].name, f'{embed.fields[0].value}\n• {name} Pack')
                    embed.edit_field(1, embed.fields[1].name, f'{embed.fields[1].value}\n{id}')
            pages.append(embed)
        for i in range(0, len(cards), items_per_page):
            embed = hikari.Embed(title=f"{self.user.username}'s Inventory", color=get_setting('embed_color'))
            # embed.set_thumbnail('assets/img/pokemon/inventory_icon.png')
            end = i + items_per_page
            for card in cards[i:end]:
                id, user_id, date, name, pokemon_id, rarity, is_shiny, favorite = card
                emoji_star = '⭐' if not is_shiny else '🌟'
                name_symbol = '' if not is_shiny else '**'
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
        self.cursor.execute("SELECT * FROM cards WHERE user_id=? ORDER BY name ASC, shiny DESC, rarity DESC, favorite DESC, date ASC;", (self.user.id,))
        cards = self.cursor.fetchall()
        self.cursor.execute("SELECT * FROM items WHERE user_id=? ORDER BY type ASC, date ASC;", (self.user.id,))
        items = self.cursor.fetchall()

        if not cards and not items:
            return None
        
        return items, cards
    
    def get_item(self, id):
        query = "SELECT * FROM items WHERE id = ? AND user_id = ?"
        self.cursor.execute(query, (id, self.user.id))
        pack = self.cursor.fetchone()
        if pack:
            return 'Pack', pack

        query = "SELECT * FROM cards WHERE id = ? AND user_id = ?"
        self.cursor.execute(query, (id, self.user.id))
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
   
    async def sell(self, cards: list) -> None:
        value = 0
        for card in cards:
            cardID = card[0]
            shiny = card[6]
            favorite = card[7]
            if favorite or not self.get_item(cardID):
                embed = hikari.Embed(title='Sell Error', description='At least one card is favorited or does not exist.', color=get_setting('embed_error_color'))
                embed.set_thumbnail('assets/img/pokemon/convert_icon.png')
                await self.ctx.edit_last_response(embed, components=[])
                return
            value += 40 if shiny else 20
        for card in cards:
            self.db.execute('DELETE FROM cards WHERE id=?', (card[0],))
        self.db.commit()
        add_money(self.user.id, value, True)

        embed = hikari.Embed(title='Success', description=f'You sold {len(cards)} cards for 🪙 {value}!', color=get_setting('embed_success_color'))
        embed.set_thumbnail('assets/img/pokemon/convert_icon.png')
        embed.set_footer('Your balance has been updated')
        await self.ctx.edit_last_response(embed, components=[])

    def __del__(self):
        self.db.close()

class NavPageInfo(nav.NavButton):
    def __init__(self, pages: int):
        super().__init__(label="Page: 1", style=hikari.ButtonStyle.SECONDARY, disabled=True)
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

@plugin.command
@lightbulb.command('inventory', 'Manage your Pokémon cards and packs inventory.')
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashCommandGroup)
async def inventory(ctx: lightbulb.Context) -> None:
    return

@inventory.child
@lightbulb.option('user', 'The user to get information about.', type=hikari.User, required=False)
@lightbulb.command('open', "Open a server member's pack inventory.", pass_options=True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def open(ctx: lightbulb.Context, user: Optional[hikari.User] = None) -> None:
    if not (guild := ctx.get_guild()):
        embed = hikari.Embed(description='This command may only be used in servers.', color=get_setting('embed_error_color'))
        await ctx.respond(embed)
        return
    elif user != None and user.is_bot: # checks if the user is a bot
        embed = hikari.Embed(description="You are not allowed to view this user's inventory!", color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return

    user = user or ctx.author
    user = ctx.bot.cache.get_member(guild, user)
    
    if not user:
        embed = hikari.Embed(description='That user is not in the server.', color=get_setting('embed_error_color'))
        await ctx.respond(embed)
        return
    
    inventory = Inventory(ctx, user)
    pages = inventory.show_inventory(10)
    buttons = [nav.FirstButton(), nav.PrevButton(emoji='⬅️'), NavPageInfo(len(pages)), nav.NextButton(emoji='➡️'), nav.LastButton()]
    navigator = nav.NavigatorView(pages=pages, buttons=buttons, timeout=None)

    await navigator.send(ctx.interaction)

## Packs Inventory Sell Command ##

class SellView(miru.View):
    def __init__(self, inventory: Inventory) -> None:
        super().__init__(timeout=None, autodefer=True)
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
        embed = hikari.Embed(title=f'Are you sure?', color=get_setting('embed_error_color'))
        embed.set_footer('This action is irreversible!')
        message = await ctx.edit_response(embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)

        await view.start(message)
        await view.wait()
        
        if view.answer:
            await self.inventory.sell(cards)
        else:
            await ctx.edit_response(hikari.Embed(description=f'Selling proccess has been cancelled.', color=get_setting('embed_error_color')), components=[], flags=hikari.MessageFlag.EPHEMERAL)
    
    async def view_check(self, ctx: ViewContext) -> bool:
        return self.inventory.get_inventory() != None


@inventory.child
@lightbulb.command('sell', "Sell your cards.", pass_options=True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def sell(ctx: lightbulb.Context) -> None:
    inventory = Inventory(ctx, ctx.author)
    embed = hikari.Embed(title='Sell Menu', description='Favorited cards will **not** be accounted for in the algorithm. \nIn the future, additional selling options may become available. \n\n> Normal = 🪙 20 \n> Shiny = 🪙 40 \n‍', color=get_setting('embed_error_color'))
    embed.set_thumbnail('assets/img/pokemon/convert_icon.png')
    embed.set_footer(text='Once you sell cards, the action cannot be undone.')
    view = SellView(inventory)
    message = await ctx.respond(embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL) 

    await view.start(message)

## Packs Open Command ##

@plugin.command
@lightbulb.option('uuid', 'Enter a pack ID you want to open.', type=str, required=True)
@lightbulb.command('open', 'Open a card pack.', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def open(ctx: lightbulb.Context, uuid: str) -> None:
    inventory = Inventory(ctx, ctx.user)
    result = inventory.get_item(uuid)

    if not result:
        embed = hikari.Embed(description='You do not own this pack!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    else:
        item_type, item = result

    if item_type == 'Card':
            embed = hikari.Embed(description='You cannot open a card!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return

    pack_id, user, date, pack_type = item
    
    if pack_type == 'Standard':
        pack = StandardPokemonCardPack(ctx.user, ctx)
    elif pack_type == 'Premium':
        pack = PremiumPokemonCardPack(ctx.user, ctx)
    
    await pack.open(pack_id)

## Packs Info Command ##

class InfoMenu(miru.View):
    def __init__(self, owner_id: str,) -> None:
        super().__init__(timeout=None)
        self.owner_id = int(owner_id)

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        if ctx.user.id != self.owner_id:
            embed = hikari.Embed(description='You are not the owner of this card!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
        return ctx.user.id == self.owner_id

class FavoriteButton(miru.Button):
    def __init__(self, embed: hikari.Embed, indents: str, card_id: str, favorite_symbol: str) -> None:
        super().__init__(emoji=favorite_symbol, style=hikari.ButtonStyle.PRIMARY, row=1, custom_id='favorite_button')
        self.db = sqlite3.connect(get_setting('database_data_dir'))
        self.cursor = self.db.cursor()
        self.embed = embed
        self.indents = indents
        self.card_id = card_id

    async def callback(self, ctx: miru.Context) -> None:
        inventory = Inventory(ctx, ctx.user)
        result = inventory.get_item(self.card_id)

        if not result:
            embed = hikari.Embed(description='This card does not exist!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        else:
            item_type, card = result
            card_id, user_id, date, name, pokemon_id, rarity, shiny, favorite = card

        favorite = not favorite
        self.cursor.execute('UPDATE cards SET favorite = ? WHERE id = ?', (int(favorite), self.card_id,))
        self.db.commit()

        if favorite:
            favorite_symbol = '<:favorite_icon:1074056642368377023>'
        else:
            favorite_symbol = '<:unfavorite_icon:1074057036393881672>'

        self.embed.title = f'{name} Card {self.indents}{favorite_symbol}' if not shiny else f'Shiny {name} Card {self.indents}{favorite_symbol}'
        self.emoji = favorite_symbol
        await ctx.edit_response(self.embed, components=self.view.build())
    
    def __del__(self):
        self.db.close()
        self.cursor.close()

class SellButton(miru.Button):
    def __init__(self, card_id: str) -> None:
        super().__init__(label='Sell Card', emoji='🗑️', style=hikari.ButtonStyle.DANGER, row=1, custom_id='trash_button')
        self.db = sqlite3.connect(get_setting('database_data_dir'))
        self.cursor = self.db.cursor()
        self.card_id = card_id

    async def callback(self, ctx: miru.Context) -> None:
        inventory = Inventory(ctx, ctx.user)
        result = inventory.get_item(self.card_id)

        if not result:
            embed = hikari.Embed(description='This card does not exist!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        else:
            item_type, card = result
            card_id, user_id, date, name, pokemon_id, rarity, shiny, favorite = card
            price = 20
            
            if shiny:
                price = price * 2

        if favorite:
            embed = hikari.Embed(description=f'You cannot sell favorited cards!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
            return

        view = PromptView()
        
        embed = hikari.Embed(title=f'Are you sure?', description=f'You will get 🪙 {price} for selling {name}.', color=get_setting('embed_error_color'))
        embed.set_footer('This action is irreversible!')
        message = await ctx.respond(embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)

        await view.start(message)
        await view.wait()
        
        if view.answer:
            if not inventory.get_item(self.card_id):
                embed = hikari.Embed(description='This card does not exist!', color=get_setting('embed_error_color'))
                await ctx.edit_response(embed, components=[], flags=hikari.MessageFlag.EPHEMERAL)
                return
            add_money(user_id, price, True)
            self.db.execute('DELETE FROM cards WHERE id=?', (card_id,))
            self.db.commit()
            await ctx.edit_response(hikari.Embed(description=f'You sold {name} for 🪙 {price}!', color=get_setting('embed_success_color')), components=[], flags=hikari.MessageFlag.EPHEMERAL)
        else:
            await ctx.edit_response(hikari.Embed(description=f'Selling proccess has been cancelled.', color=get_setting('embed_error_color')), components=[], flags=hikari.MessageFlag.EPHEMERAL)
        
    
    def __del__(self):
        self.db.close()
        self.cursor.close()

@plugin.command
@lightbulb.option('uuid', 'Enter a pack or card ID to get more info on it.', type=str, required=True)
@lightbulb.command('info', 'View additional info on a card or pack.', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def open(ctx: lightbulb.Context, uuid: str) -> None:
    db = sqlite3.connect(get_setting('database_data_dir'))
    cursor = db.cursor()
    
    result = None

    cursor.execute("SELECT * FROM items WHERE id = ?", (uuid,))
    pack = cursor.fetchone()
    if pack:
        result = 'Pack', pack

    cursor.execute("SELECT * FROM cards WHERE id = ?", (uuid,))
    card = cursor.fetchone()
    if card:
        result = 'Card', card

    if not result:
        embed = hikari.Embed(description='Card or pack was not found!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return

    item_type, item = result
    if item_type == 'Pack':
        pack_id, user_id, date, pack_type = item
        view = InfoMenu(user_id)
        embed = hikari.Embed(title=f'{pack_type} Pack', description='A standard pack that contains 7 Pokémon cards.' if pack_type == 'Standard' else 'A premium pack that contains 7 high quality Pokémon cards.', color=get_setting('embed_color'))
        embed.set_thumbnail(f'assets/img/pokemon/{pack_type.lower()}_pack_icon.png')
        embed.add_field(name='Owner', value=f'<@{user_id}>', inline=True)
        embed.add_field(name='Obtained', value=date, inline=True)
        embed.add_field(name='Pack ID', value=f'`{pack_id}`', inline=False)
        embed.set_footer('Type `/shop` to buy packs!')
    elif item_type == 'Card':
        card_id, user_id, date, name, pokemon_id, rarity, is_shiny, favorite = item
        view = InfoMenu(user_id)

        if is_shiny:
            rarity_symbol = '🌟'
            shiny = True
            indents = '\t\t\t\t\t\t\t\t\t'
        else:
            rarity_symbol = '⭐'
            shiny = False
            indents = '\t\t\t\t\t\t\t\t\t\t\t'
        
        if favorite:
            favorite_symbol = '<:favorite_icon:1074056642368377023>'
        else:
            favorite_symbol = '<:unfavorite_icon:1074057036393881672>'
        
        embed = hikari.Embed(title=f'{name} Card {indents}{favorite_symbol}' if not shiny else f'Shiny {name} Card {indents}{favorite_symbol}', color=get_setting('embed_color'))
        embed.set_image(f'https://img.pokemondb.net/sprites/home/normal/{name.lower()}.png' if not shiny else f'https://img.pokemondb.net/sprites/home/shiny/{name.lower()}.png')
        # embed.set_image(f'https://raw.githubusercontent.com/harshit23897/Pokemon-Sprites/master/assets/imagesHQ/{"{:03d}".format(pokemon_id)}.png') # If you want 2d sprites. This does not support shiny sprites.
        embed.add_field(name='Owner', value=f'<@{user_id}>', inline=True)
        embed.add_field(name='Obtained', value=date, inline=True)
        embed.add_field(name='Pokémon ID', value=pokemon_id, inline=True)
        embed.add_field(name='Pokémon Name', value=name, inline=True)
        embed.add_field(name='Card Quality', value=" ".join([rarity_symbol for i in range(rarity)]), inline=True)
        embed.add_field(name='Card ID', value=f'`{card_id}`', inline=False)
        embed.set_footer('Type `/shop` to get Pokémon cards!')

        view.add_item(FavoriteButton(embed, indents, card_id, favorite_symbol))
        view.add_item(SellButton(card_id))

    message = await ctx.respond(embed, components=view.build())
    await view.start(message)

## Packs Trade Command ##

class TradeView(miru.View):
    def __init__(self, ctx: lightbulb.Context, embed: hikari.Embed, user1: hikari.User, user2: hikari.User) -> None:
        super().__init__(timeout=120)
        self.db = sqlite3.connect(get_setting('database_data_dir'))
        self.cursor = self.db.cursor()
        self.ctx = ctx
        self.embed = embed
        self.user1 = user1
        self.user1_ready = False
        self.user1_offer = []
        self.user2 = user2
        self.user2_ready = False
        self.user2_offer = []
    
    @miru.button(label='Item', emoji='➕', style=hikari.ButtonStyle.SUCCESS, row=1, custom_id='add_item')
    async def include_item(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        user = (self.user1, self.user1_offer) if ctx.user.id == self.user1.id else (self.user2, self.user2_offer)
        modal = AddItemModal(user)
        await ctx.respond_with_modal(modal)
        await modal.wait()

        if not modal.item:
            return

        item_type, item = modal.item

        if item_type == 'Pack':
            item_id, user_id, date, name = item
        elif item_type == 'Card':
            item_id, user_id, date, name, pokemon_id, rarity, shiny, favorite = item

        if ctx.user.id == self.user1.id:
            self.user1_ready = False
            self.user1_offer.append((item_type, item_id))
        else:
            self.user2_ready = False
            self.user2_offer.append((item_type, item_id))
        
        await self.update_trade_display()

    @miru.button(label='Ready', style=hikari.ButtonStyle.SUCCESS, row=1, custom_id='ready')
    async def ready(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        if ctx.user.id == self.user1.id:
            if not self.user1_ready:
                self.user1_ready = True
                self.embed.edit_field(0, f'{self.embed.fields[0].name} ✅', self.embed.fields[0].value)
            else:
                self.user1_ready = False
                self.embed.edit_field(0, f'{self.user1.username} Trade Offer', self.embed.fields[0].value)
        else:
            if not self.user2_ready:
                self.user2_ready = True
                self.embed.edit_field(1, f'{self.embed.fields[1].name} ✅', self.embed.fields[1].value)
            else:
                self.user2_ready = False
                self.embed.edit_field(1, f'{self.user2.username} Trade Offer', self.embed.fields[1].value)
        
        if self.user1_ready and self.user2_ready:
            self.complete_trade()
            self.embed.title = 'Trade has been completed!'
            self.embed.color = get_setting('embed_success_color')
            await ctx.edit_response(self.embed, components=[])
            self.stop()
            return

        await ctx.edit_response(self.embed)

    @miru.button(label='Item', emoji='🗑️', style=hikari.ButtonStyle.DANGER, row=1, custom_id='remove_item')
    async def remove_item(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        user = (self.user1, self.user1_offer) if ctx.user.id == self.user1.id else (self.user2, self.user2_offer)
        modal = RemoveItemModal(user)
        await ctx.respond_with_modal(modal)
        await modal.wait()

        if not modal.item_index:
            return
        elif ctx.user.id == self.user1.id:
            self.user1_ready = False
            self.user1_offer.pop(modal.item_index-1)
        else:
            self.user2_ready = False
            self.user2_offer.pop(modal.item_index-1)
        
        await self.update_trade_display()
    
    @miru.button(label='Exit', style=hikari.ButtonStyle.DANGER, row=1, custom_id='exit')
    async def exit(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        self.embed.title = f'{self.user1.username} has declined the trade!' if ctx.user.id == self.user1.id else f'{self.user2.username} has declined the trade!'
        self.embed.color = get_setting('embed_error_color')
        await ctx.edit_response(self.embed, components=[])
        self.stop()

    async def on_timeout(self) -> None:
        self.embed.title = f'Trade menu has timed out!'
        await self.ctx.edit_last_response(self.embed, components=[])
        self.stop()
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.user1.id or ctx.user.id == self.user2.id
    
    async def update_trade_display(self) -> None:
        user1_offer = []
        user2_offer = []

        for item_type, item_id in self.user1_offer:
            if item_type == 'Pack':
                self.cursor.execute('SELECT type FROM items WHERE id = ?', (item_id,))
                item = f'• {self.cursor.fetchone()[0]} Pack'
            elif item_type == 'Card':
                self.cursor.execute('SELECT name, rarity, shiny FROM cards WHERE id = ?', (item_id,))
                name, rarity, shiny = self.cursor.fetchone()
                if shiny:
                    rarity_symbol = '🌟'
                else:
                    rarity_symbol = '⭐'
                
                item = f'• {name} {" ".join([rarity_symbol for i in range(rarity)])}'
            user1_offer.append(item)
        for item_type, item_id in self.user2_offer:
            if item_type == 'Pack':
                self.cursor.execute('SELECT type FROM items WHERE id = ?', (item_id,))
                item = f'• {self.cursor.fetchone()[0]} Pack'
            elif item_type == 'Card':
                self.cursor.execute('SELECT name, rarity, shiny FROM cards WHERE id = ?', (item_id,))
                name, rarity, shiny = self.cursor.fetchone()

                if shiny:
                    rarity_symbol = '🌟'
                else:
                    rarity_symbol = '⭐'
                    
                item = f'• {name} {" ".join([rarity_symbol for i in range(rarity)])}'
            user2_offer.append(item)
        
        user1_offer_string = '\n'.join(user1_offer + ['• -' for i in range(10-len(user1_offer))])
        user2_offer_string = '\n'.join(user2_offer + ['• -' for i in range(10-len(user2_offer))])

        self.embed.edit_field(0, self.embed.fields[0].name, f'`Item Limit: {len(user1_offer)}/10`\n{user1_offer_string}' if len(user1_offer) > 0 else f'`Item Limit: 0/10`\n' + '\n'.join(['• -' for i in range(10)]))
        self.embed.edit_field(1, self.embed.fields[1].name, f'`Item Limit: {len(user2_offer)}/10`\n{user2_offer_string}' if len(user2_offer) > 0 else f'`Item Limit: 0/10`\n' + '\n'.join(['• -' for i in range(10)]))
        await self.ctx.edit_last_response(self.embed)
    
    def complete_trade(self) -> None:
        db = sqlite3.connect(get_setting('database_data_dir'))
        cursor = db.cursor()
        for item in self.user1_offer:
            item_type, item_id = item
            if item_type == 'Pack':
                cursor.execute('UPDATE items SET user_id = ? WHERE id = ?', (self.user2.id, item_id))
            elif item_type == 'Card':
                cursor.execute('UPDATE cards SET user_id = ? WHERE id = ?', (self.user2.id, item_id))
            db.commit()
        for item in self.user2_offer:
            item_type, item_id = item
            if item_type == 'Pack':
                cursor.execute('UPDATE items SET user_id = ? WHERE id = ?', (self.user1.id, item_id))
            elif item_type == 'Card':
                cursor.execute('UPDATE cards SET user_id = ? WHERE id = ?', (self.user1.id, item_id))
            db.commit()
        db.close()

class AddItemModal(miru.Modal):
    id = miru.TextInput(label='Enter Item UUID', placeholder='25aea761-7725-41da-969f-5d55a6af1519', custom_id='add_item_input', style=hikari.TextInputStyle.SHORT, required=True)

    def __init__(self, user: tuple) -> None:
        super().__init__(title='Add Item Menu', custom_id='add_item_menu', timeout=None)
        self.user, self.user_offer = user
        self.item = None
    
    async def callback(self, ctx: miru.ModalContext) -> None:
        inventory = Inventory(ctx, ctx.user)
        result = inventory.get_item(self.id.value)

        if not result:
            embed = hikari.Embed(title='Item Error', description='You do not own this item!', color=get_setting('embed_error_color'))
            embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
            self.stop()
            return
        elif len(self.user_offer) >= 10:
            embed = hikari.Embed(title='Item Error', description='You reached the item limit!', color=get_setting('embed_error_color'))
            embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
            self.stop()
            return
        else:
            self.item = result
            item_type, item = self.item
            
            if item_type == 'Pack':
                item_id, user_id, date, name = item
                name = f'{name} Booster Pack'
            elif item_type == 'Card':
                item_id, user_id, date, name, pokemon_id, rarity, shiny, favorite = item
        
        for item in self.user_offer:
            if item_id in item:
                embed = hikari.Embed(title='Item Error', description='You already added this item!', color=get_setting('embed_error_color'))
                embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
                self.item = None
                break
        else:
            embed = hikari.Embed(title='Item Added', description=f'You added {name} (`{item_id}`) to the trade.', color=get_setting('embed_success_color'))
            embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
        
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)

class RemoveItemModal(miru.Modal):
    val = miru.TextInput(label='Enter Item Index', placeholder='1 - 10', custom_id='remove_item_input', style=hikari.TextInputStyle.SHORT, required=True)

    def __init__(self, user: tuple) -> None:
        super().__init__(title='Remove Item Menu', custom_id='remove_item_menu', timeout=None)
        self.user, self.user_offer = user
        self.item_index = 0
    
    async def callback(self, ctx: miru.ModalContext) -> None:
        try:
            if int(self.val.value) > len(self.user_offer) or int(self.val.value) < 1:
                embed = hikari.Embed(title='Item Error', description='Invalid index!', color=get_setting('embed_error_color'))
                embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
                self.item_index = None
                self.stop()
                return
            else:
                self.item_index = int(self.val.value)
        except ValueError:
            embed = hikari.Embed(title='Item Error', description='Input is not a number!', color=get_setting('embed_error_color'))
            embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
            self.item_index = None
            self.stop()
            return
        
        embed = hikari.Embed(title='Item Removed', description=f'{self.user_offer[self.item_index-1][0]} was removed.', color=get_setting('embed_error_color'))
        embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)

@plugin.command
@lightbulb.option('user', 'The user to trade with.', type=hikari.User, required=True)
@lightbulb.command('trade', "Trade items or cards with a server member.", pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def trade(ctx: lightbulb.Context, user: hikari.User) -> None:
    if user.is_bot or ctx.author.id == user.id: # checks if the user is a bot or the sender
        embed = hikari.Embed(description='You are not allowed to trade with this user!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
        return
    
    embed = hikari.Embed(title=f'Trading with {user.username}...', description='Use the buttons below to edit the Items/Cards in your trade.', color=get_setting('embed_color'))
    embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
    embed.add_field(name=f'{ctx.author.username} Trade Offer', value='`Item Limit: 0/10`\n' + '\n'.join(['• -' for i in range(10)]), inline=True)
    embed.add_field(name=f'{user.username} Trade Offer', value='`Item Limit: 0/10`\n' + '\n'.join(['• -' for i in range(10)]), inline=True)
    embed.set_footer('Trade menu will time out in 2 minutes.')

    view = TradeView(ctx, embed, ctx.author, user)
    message = await ctx.respond(embed, components=view.build())
    
    await view.start(message)
    await view.wait()

## Error Handler ##

@plugin.set_error_handler()
async def on_command_error(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event.exception, lightbulb.CommandNotFound):
        return
    if isinstance(event.exception, lightbulb.NotEnoughArguments):
        embed = (hikari.Embed(description='Not enough arguments were passed.\n' + ', '.join(event.exception.args), color=get_setting('embed_error_color')))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    if isinstance(event.exception, lightbulb.CommandIsOnCooldown):
        embed = (hikari.Embed(description=f'Command is on cooldown. Try again in {round(event.exception.retry_after)} second(s).', color=get_setting('embed_error_color')))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    if isinstance(event.exception, lightbulb.NotOwner):
        embed = (hikari.Embed(description=f'You do not have permission to use this command!', color=get_setting('embed_error_color')))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    embed = (hikari.Embed(description='I have errored, and I cannot get up', color=get_setting('embed_error_color')))
    await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    raise event.exception

## Definitions ##

def load(bot):
    bot.add_plugin(plugin)