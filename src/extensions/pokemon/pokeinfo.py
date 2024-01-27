import hikari
import lightbulb
import miru
import sqlite3

from bot import get_setting
from utils.economy.manager import EconomyManager
from utils.pokemon.inventory import Inventory, PromptView

plugin = lightbulb.Plugin('Pokeinfo')
economy = EconomyManager()

class InfoMenu(miru.View):
    def __init__(self, owner_id: str,) -> None:
        super().__init__(timeout=None)
        self.owner_id = int(owner_id)

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        if ctx.user.id != self.owner_id:
            embed = hikari.Embed(description='You are not the owner of this card!', color=get_setting('settings', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
        return ctx.user.id == self.owner_id

class FavoriteButton(miru.Button):
    def __init__(self, embed: hikari.Embed, indents: str, card_id: str, favorite_symbol: str) -> None:
        super().__init__(emoji=favorite_symbol, style=hikari.ButtonStyle.PRIMARY, row=1, custom_id='favorite_button')
        self.db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        self.cursor = self.db.cursor()
        self.embed = embed
        self.indents = indents
        self.card_id = card_id

    async def callback(self, ctx: miru.Context) -> None:
        inventory = Inventory(ctx, ctx.user)
        result = inventory.get_item(self.card_id)

        if not result:
            embed = hikari.Embed(description='This card does not exist!', color=get_setting('settings', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        else:
            name, card = result
            card_id, userID, date, name, pokemon_id, rarity, shiny, favorite = card

        favorite = not favorite
        self.cursor.execute('UPDATE pokemon SET favorite = ? WHERE id = ?', (int(favorite), self.card_id,))
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
        self.db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
        self.cursor = self.db.cursor()
        self.card_id = card_id

    async def callback(self, ctx: miru.Context) -> None:
        inventory = Inventory(ctx, ctx.user)
        result = inventory.get_item(self.card_id)

        if not result:
            embed = hikari.Embed(description='This card does not exist!', color=get_setting('settings', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        else:
            name, card = result
            card_id, userID, date, name, pokemon_id, rarity, shiny, favorite = card
            price = 20
            
            if shiny:
                price = price * 2

        if favorite:
            embed = hikari.Embed(description=f'You cannot sell favorited cards!', color=get_setting('settings', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
            return

        view = PromptView()
        
        embed = hikari.Embed(title=f'Are you sure?', description=f'You will get 🪙 {price} for selling {name}.', color=get_setting('settings', 'embed_error_color'))
        embed.set_footer('This action is irreversible!')
        message = await ctx.respond(embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)

        await view.start(message)
        await view.wait()
        
        if view.answer:
            if not inventory.get_item(self.card_id):
                embed = hikari.Embed(description='This card does not exist!', color=get_setting('settings', 'embed_error_color'))
                await ctx.edit_response(embed, components=[], flags=hikari.MessageFlag.EPHEMERAL)
                return
            economy.add_money(userID, price, True)
            try:
                self.db.execute('DELETE FROM pokemon WHERE id = ?', (card_id,))
                self.db.commit()
            except sqlite3.Error as e:
                self.db.rollback()
                print("Error deleting item from the database:", e)
            await ctx.edit_response(hikari.Embed(description=f'You sold {name} for 🪙 {price}!', color=get_setting('settings', 'embed_success_color')), components=[], flags=hikari.MessageFlag.EPHEMERAL)
        else:
            await ctx.edit_response(hikari.Embed(description=f'Selling proccess has been cancelled.', color=get_setting('settings', 'embed_error_color')), components=[], flags=hikari.MessageFlag.EPHEMERAL)
    
    def __del__(self):
        self.db.close()
        self.cursor.close()

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('uuid', 'Enter a pack or card ID to get more info on it.', type=str, required=True)
@lightbulb.command('pokeinfo', 'Obtain additional details on a Pokémon card or pack.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def open(ctx: lightbulb.Context, uuid: str) -> None:
    db = sqlite3.connect(get_setting('settings', 'database_data_dir'))
    cursor = db.cursor()
    
    result = None

    cursor.execute("SELECT id, user_id, date, name FROM pokemon WHERE id = ? AND name IN (?, ?)", (uuid, 'Standard', 'Premium'))
    pack = cursor.fetchone()
    if pack:
        result = 'Pack', pack

    cursor.execute("SELECT * FROM pokemon WHERE id = ? AND name NOT IN (?, ?)", (uuid, 'Standard', 'Premium'))
    card = cursor.fetchone()
    if card:
        result = 'Card', card

    if not result:
        embed = hikari.Embed(description='Card or pack was not found!', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return

    name, item = result
    if name == 'Pack':
        packID, userID, date, pack_type = item
        view = InfoMenu(userID)
        embed = hikari.Embed(title=f'{pack_type} Pack', description='A standard pack that contains 7 Pokémon cards.' if pack_type == 'Standard' else 'A premium pack that contains 7 high quality Pokémon cards.', color=get_setting('settings', 'embed_color'))
        embed.set_thumbnail(f'assets/img/pokemon/{pack_type.lower()}_pack_icon.png')
        embed.add_field(name='Owner', value=f'<@{userID}>', inline=True)
        embed.add_field(name='Obtained', value=date, inline=True)
        embed.add_field(name='Pack ID', value=f'`{packID}`', inline=False)
        embed.set_footer('Type `/packshop` to buy packs!')
    elif name == 'Card':
        card_id, userID, date, name, pokemon_id, rarity, is_shiny, favorite = item
        view = InfoMenu(userID)

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
        
        embed = hikari.Embed(title=f'{name} Card {indents}{favorite_symbol}' if not shiny else f'Shiny {name} Card {indents}{favorite_symbol}', color=get_setting('settings', 'embed_color'))
        embed.set_image(f'https://img.pokemondb.net/sprites/home/normal/{name.lower()}.png' if not shiny else f'https://img.pokemondb.net/sprites/home/shiny/{name.lower()}.png')
        # embed.set_image(f'https://raw.githubusercontent.com/harshit23897/Pokemon-Sprites/master/assets/imagesHQ/{"{:03d}".format(pokemon_id)}.png') # If you want 2d sprites. This does not support shiny sprites.
        embed.add_field(name='Owner', value=f'<@{userID}>', inline=True)
        embed.add_field(name='Obtained', value=date, inline=True)
        embed.add_field(name='Pokémon ID', value=pokemon_id, inline=True)
        embed.add_field(name='Pokémon Name', value=name, inline=True)
        embed.add_field(name='Card Quality', value=" ".join([rarity_symbol for i in range(rarity)]), inline=True)
        embed.add_field(name='Card ID', value=f'`{card_id}`', inline=False)
        embed.set_footer('Type `/packshop` to get Pokémon cards!')

        view.add_item(FavoriteButton(embed, indents, card_id, favorite_symbol))
        view.add_item(SellButton(card_id))

    message = await ctx.respond(embed, components=view.build())
    await view.start(message)

def load(bot):
    bot.add_plugin(plugin)