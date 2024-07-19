import hikari
import miru
import random
import sqlite3
import requests
import uuid
import datetime
import pytz

from bot import get_setting
from miru.ext import nav
from utils.pokemon.card import PokemonCard

timezone = pytz.timezone("America/New_York")

class PokemonPack:
    def __init__(self, user: hikari.User, packID, pack_type):
        self.user = user
        self.packID = packID
        self.pack_type = pack_type

class StandardPokemonCardPack:
    def __init__(self, ctx: miru.ViewContext, user: hikari.User):
        self.user = user
        self.ctx = ctx
    
    async def buy(self):
        self.db = sqlite3.connect(get_setting('general', 'database_data_dir'))
        self.cursor = self.db.cursor()
        
        packID = str(uuid.uuid4())
        current_date = datetime.datetime.now(timezone)
        date = current_date.strftime('%m/%d/%Y')
        pack_type = 'Standard'

        try:
            self.cursor.execute('INSERT INTO pokemon (id, user_id, date, name, pokemon_id, rarity, shiny, favorite) VALUES (?,?,?,?,?,?,?,?)', (packID, self.user.id, date, pack_type, None, None, None, None))
            self.db.commit()
        except sqlite3.Error as e:
            self.db.rollback()
            print("Error inserting item from the database:", e)

        embed = hikari.Embed(title='Pokémon Booster Pack Shop', description=f'Thank you for your purchase <@{self.user.id}>!\nPack ID: `{packID}`', color=get_setting('general', 'embed_success_color'))
        embed.set_thumbnail('assets/img/pokemon/shop_icon.png')
        await self.ctx.respond(embed, delete_after=30)

    async def open(self, packID):
        self.cards = []
        
        self.db = sqlite3.connect(get_setting('general', 'database_data_dir'))
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
            try:
                self.cursor.execute("INSERT INTO pokemon (id, user_id, date, name, pokemon_id, rarity, shiny, favorite) VALUES (?,?,?,?,?,?,?,?)", (card_id, self.user.id, date, pokemon_data["name"].capitalize(), pokemon_data["id"], rarity, int(shiny), int(favorite)))
                self.db.commit()
            except sqlite3.Error as e:
                self.db.rollback()
                print("Error inserting item from the database:", e)
        try:
            self.db.execute('DELETE FROM pokemon WHERE id=?', (packID,))
            self.db.commit()
        except sqlite3.Error as e:
            self.db.rollback()
            print("Error deleting item from the database:", e)

        embed = hikari.Embed(title=f'Standard Booster Pack Overview', color=get_setting('general', 'embed_color'))
        embed.set_footer('Type `/packinventory view` to view your cards and packs.')

        pages = []
        for card in self.cards:
            pages = card.display(pages)
            embed = card.display_overview(embed)
        pages.append(embed)
        
        buttons = [nav.PrevButton(emoji='⬅️', row=1), NavPageInfo(len(pages), row=1), nav.NextButton(emoji='➡️', row=1), nav.LastButton(row=1)]
        navigator = ChecksView(self.user, pages, buttons, timeout=None)
        builder = await navigator.build_response_async(client=self.ctx.client, ephemeral=True)
        await builder.create_initial_response(self.ctx.interaction)
        self.ctx.client.start_view(navigator)

    def __del__(self):
        self.db.close()

class PremiumPokemonCardPack:
    def __init__(self, user: hikari.User, ctx: miru.ViewContext):
        self.user = user
        self.ctx = ctx
    
    async def buy(self):
        self.db = sqlite3.connect(get_setting('general', 'database_data_dir'))
        self.cursor = self.db.cursor()
        
        packID = str(uuid.uuid4())
        current_date = datetime.datetime.now(timezone)
        date = current_date.strftime('%m/%d/%Y')
        pack_type = 'Premium'

        try:
            self.cursor.execute("INSERT INTO pokemon (id, user_id, date, name, pokemon_id, rarity, shiny, favorite) VALUES (?,?,?,?,?,?,?,?)", (packID, self.user.id, date, pack_type, None, None, None, None))
            self.db.commit()
        except sqlite3.Error as e:
            self.db.rollback()
            print("Error inserting item from the database:", e)

        embed = hikari.Embed(title='Pokémon Booster Pack Shop', description=f'Thank you for your purchase <@{self.user.id}>!\nPack ID: `{packID}`', color=get_setting('general', 'embed_success_color'))
        embed.set_thumbnail('assets/img/pokemon/shop_icon.png')
        embed.set_footer('Type `/packinventory view` to see your packs!')
        await self.ctx.respond(embed, delete_after=30)

    async def open(self, packID):
        self.cards = []
        
        self.db = sqlite3.connect(get_setting('general', 'database_data_dir'))
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
            try:
                self.cursor.execute("INSERT INTO pokemon (id, user_id, date, name, pokemon_id, rarity, shiny, favorite) VALUES (?,?,?,?,?,?,?,?)", (card_id, self.user.id, date, pokemon_data["name"].capitalize(), pokemon_data["id"], rarity, int(shiny), int(favorite)))
                self.db.commit()
            except sqlite3.Error as e:
                self.db.rollback()
                print("Error inserting item from the database:", e)
        try:
            self.db.execute('DELETE FROM pokemon WHERE id=?', (packID,))
            self.db.commit()
        except sqlite3.Error as e:
            self.db.rollback()
            print("Error deleting item from the database:", e)

        embed = hikari.Embed(title=f'Premium Booster Pack Overview', color=get_setting('general', 'embed_color'))
        embed.set_footer('Type `/packinventory view` to view your cards and packs.')

        pages = []
        for card in self.cards:
            pages = card.display(pages)
            embed = card.display_overview(embed)
        pages.append(embed)
        
        buttons = [nav.PrevButton(emoji='⬅️'), NavPageInfo(len(pages)), nav.NextButton(emoji='➡️'), nav.LastButton()]
        navigator = nav.NavigatorView(pages=pages, items=buttons, timeout=None)
        builder = await navigator.build_response_async(client=self.ctx.client, ephemeral=True)
        await builder.create_initial_response(self.ctx.interaction)
        self.ctx.client.start_view(navigator)

    def __del__(self):
        self.db.close()

class ChecksView(nav.NavigatorView):
    def __init__(self, user: hikari.User, pages, buttons, timeout, autodefer: bool = True) -> None:
        super().__init__(pages=pages, items=buttons, timeout=timeout, autodefer=autodefer)
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