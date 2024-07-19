import hikari
import lightbulb
import miru
import sqlite3

from bot import get_setting
from utils.pokemon.inventory import Inventory

plugin = lightbulb.Plugin('Poketrade')

class TradeView(miru.View):
    def __init__(self, ctx: lightbulb.Context, embed: hikari.Embed, user1: hikari.User, user2: hikari.User) -> None:
        super().__init__(timeout=120)
        self.db = sqlite3.connect(get_setting('general', 'database_data_dir'))
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

        name, item = modal.item

        if name == 'Pack':
            itemID, userID, date, name = item
        elif name == 'Card':
            itemID, userID, date, name, pokemon_id, rarity, shiny, favorite = item

        if ctx.user.id == self.user1.id:
            self.user1_ready = False
            self.user1_offer.append((name, itemID))
        else:
            self.user2_ready = False
            self.user2_offer.append((name, itemID))
        
        await self.update_trade_display()

    @miru.button(label='Ready', style=hikari.ButtonStyle.SUCCESS, row=1, custom_id='ready')
    async def ready(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        if ctx.user.id == self.user1.id:
            if not self.user1_ready:
                self.user1_ready = True
                self.embed.edit_field(0, f'{self.embed.fields[0].name} ✅', self.embed.fields[0].value)
            else:
                self.user1_ready = False
                self.embed.edit_field(0, f'{self.user1.global_name} Trade Offer', self.embed.fields[0].value)
        else:
            if not self.user2_ready:
                self.user2_ready = True
                self.embed.edit_field(1, f'{self.embed.fields[1].name} ✅', self.embed.fields[1].value)
            else:
                self.user2_ready = False
                self.embed.edit_field(1, f'{self.user2.global_name} Trade Offer', self.embed.fields[1].value)
        
        if self.user1_ready and self.user2_ready:
            user1Inv = Inventory(self.ctx, self.user1)
            user2Inv = Inventory(self.ctx, self.user2)
            if user1Inv.get_inventory_capacity() + len(self.user2_offer) > user1Inv.max:
                self.embed.title = 'Trade Error!'
                self.embed.description = f'{self.user1.global_name} does not have enough inventory space!'
                self.embed.color = get_setting('general', 'embed_error_color')
                self.embed.set_footer(None)
                self.stop()
                return await self.ctx.edit_last_response(self.embed, components=[])
            elif user2Inv.get_inventory_capacity() + len(self.user1_offer) > user2Inv.max:
                self.embed.title = 'Trade Error!'
                self.embed.description = f'{self.user2.global_name} does not have enough inventory space!'
                self.embed.color = get_setting('general', 'embed_error_color')
                self.embed.set_footer(None)
                self.stop()
                return await self.ctx.edit_last_response(self.embed, components=[])
            else:
                for item in self.user1_offer:
                    name, itemID = item
                    if user1Inv.get_item(itemID) == None:
                        self.embed.title = 'Trade Error!'
                        self.embed.description = f'{self.user1.global_name} no longer owns card(s) or pack(s)!'
                        self.embed.color = get_setting('general', 'embed_error_color')
                        self.embed.set_footer(None)
                        self.stop()
                        return await self.ctx.edit_last_response(self.embed, components=[])
                for item in self.user2_offer:
                    name, itemID = item
                    if user2Inv.get_item(itemID) == None:
                        self.embed.title = 'Trade Error!'
                        self.embed.description = f'{self.user2.global_name} no longer owns card(s) or pack(s)!'
                        self.embed.color = get_setting('general', 'embed_error_color')
                        self.embed.set_footer(None)
                        self.stop()
                        return await self.ctx.edit_last_response(self.embed, components=[])
                self.complete_trade()
                self.embed.title = 'Trade has been completed!'
                self.embed.color = get_setting('general', 'embed_success_color')
                self.stop()
                return await ctx.edit_response(self.embed, components=[])

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
        self.embed.title = f'{self.user1.global_name} has declined the trade!' if ctx.user.id == self.user1.id else f'{self.user2.global_name} has declined the trade!'
        self.embed.color = get_setting('general', 'embed_error_color')
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

        for name, itemID in self.user1_offer:
            if name in ['Standard', 'Premium']:
                self.cursor.execute('SELECT name FROM pokemon WHERE id = ?', (itemID,))
                item = f'• {self.cursor.fetchone()[0]} Pack'
            else:
                self.cursor.execute('SELECT name, rarity, shiny FROM pokemon WHERE id = ?', (itemID,))
                name, rarity, shiny = self.cursor.fetchone()
                if shiny:
                    rarity_symbol = '🌟'
                else:
                    rarity_symbol = '⭐'
                
                item = f'• {name} {" ".join([rarity_symbol for i in range(rarity)])}'
            user1_offer.append(item)
        for name, itemID in self.user2_offer:
            if name == 'Pack':
                self.cursor.execute('SELECT type FROM pokemon WHERE id = ?', (itemID,))
                item = f'• {self.cursor.fetchone()[0]} Pack'
            elif name == 'Card':
                self.cursor.execute('SELECT name, rarity, shiny FROM pokemon WHERE id = ?', (itemID,))
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
        db = sqlite3.connect(get_setting('general', 'database_data_dir'))
        cursor = db.cursor()
        for item in self.user1_offer:
            name, itemID = item
            cursor.execute('UPDATE pokemon SET user_id = ? WHERE id = ?', (self.user2.id, itemID))
            db.commit()
        for item in self.user2_offer:
            name, itemID = item
            cursor.execute('UPDATE pokemon SET user_id = ? WHERE id = ?', (self.user1.id, itemID))
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
            embed = hikari.Embed(title='Item Error', description='You do not own this item!', color=get_setting('general', 'embed_error_color'))
            embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
            self.stop()
            return
        elif len(self.user_offer) >= 10:
            embed = hikari.Embed(title='Item Error', description='You reached the item limit!', color=get_setting('general', 'embed_error_color'))
            embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
            self.stop()
            return
        else:
            self.item = result
            name, item = self.item
            
            if name == 'Pack':
                itemID, userID, date, name = item
                name = f'{name} Booster Pack'
            elif name == 'Card':
                itemID, userID, date, name, pokemon_id, rarity, shiny, favorite = item
        
        for item in self.user_offer:
            if itemID in item:
                embed = hikari.Embed(title='Item Error', description='You already added this item!', color=get_setting('general', 'embed_error_color'))
                embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
                self.item = None
                break
        else:
            embed = hikari.Embed(title='Item Added', description=f'You added {name} (`{itemID}`) to the trade.', color=get_setting('general', 'embed_success_color'))
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
                embed = hikari.Embed(title='Item Error', description='Invalid index!', color=get_setting('general', 'embed_error_color'))
                embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
                self.item_index = None
                self.stop()
                return
            else:
                self.item_index = int(self.val.value)
        except ValueError:
            embed = hikari.Embed(title='Item Error', description='Input is not a number!', color=get_setting('general', 'embed_error_color'))
            embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
            self.item_index = None
            self.stop()
            return
        
        embed = hikari.Embed(title='Item Removed', description=f'{self.user_offer[self.item_index-1][0]} was removed.', color=get_setting('general', 'embed_error_color'))
        embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('user', 'The user to trade with.', type=hikari.User, required=True)
@lightbulb.command('poketrade', 'Initiate a Pokémon item or card trade with a Discord member.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def trade(ctx: lightbulb.Context, user: hikari.User) -> None:
    if user.is_bot or ctx.author.id == user.id: # checks if the user is a bot or the sender
        embed = hikari.Embed(description='You are not allowed to trade with this user!', color=get_setting('general', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL, delete_after=10)
        return
    
    embed = hikari.Embed(title=f'Trading with {user.global_name}...', description='Use the buttons below to edit the Items/Cards in your trade.', color=get_setting('general', 'embed_color'))
    embed.set_thumbnail('assets/img/pokemon/trade_icon.png')
    embed.add_field(name=f'{ctx.author.global_name} Trade Offer', value='`Item Limit: 0/10`\n' + '\n'.join(['• -' for i in range(10)]), inline=True)
    embed.add_field(name=f'{user.global_name} Trade Offer', value='`Item Limit: 0/10`\n' + '\n'.join(['• -' for i in range(10)]), inline=True)
    embed.set_footer('Trade menu will time out in 2 minutes.')

    view = TradeView(ctx, embed, ctx.author, user)
    message = await ctx.respond(embed, components=view.build())
    
    await view.start(message)
    await view.wait()

def load(bot):
    bot.add_plugin(plugin)