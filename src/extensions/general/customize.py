import hikari
import lightbulb
import miru
import sqlite3

from miru.context import ViewContext
from miru.context.view import ViewContext
from PIL import Image

from bot import get_setting
from utils.profile.inventory import Inventory
from utils.profile.card import Card

plugin = lightbulb.Plugin('Customize')

class ProfileCustomizeView(miru.View):
    def __init__(self, inventory: Inventory, profile: Card, newPreset: list) -> None:
        super().__init__(timeout=None, autodefer=True)
        self.db = sqlite3.connect(get_setting('general', 'database_data_dir'))
        self.cursor = self.db.cursor()
        self.inventory = inventory
        self.profile = profile
        self.newPreset = newPreset

    @miru.button(label='Save', emoji='🖨️', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def save(self, button: miru.Button, ctx: miru.ViewContext):
        self.cursor.execute('UPDATE profile SET active = 0 WHERE user_id = ?', (ctx.user.id,))
        for item in self.newPreset:
            name, type = str(item).split('-')
            self.cursor.execute('UPDATE profile SET active = 1 WHERE user_id = ? AND name = ? AND type = ?', (ctx.user.id, name, type))
        self.db.commit()

        embed = hikari.Embed(description='Profile has been saved!', color=get_setting('general', 'embed_success_color'))
        await ctx.edit_response(components=[])
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        self.stop()
    
    @miru.button(label='Cancel', emoji='✖️', style=hikari.ButtonStyle.DANGER, row=1)
    async def cancel(self, button: miru.Button, ctx: miru.ViewContext):
        await ctx.edit_response(components=[])
        self.stop()
    
    @miru.button(label='Preview', emoji='🔍', style=hikari.ButtonStyle.PRIMARY, row=1)
    async def preview(self, button: miru.Button, ctx: miru.ViewContext):
        bg = Image.open(f'assets/img/general/profile/banner/{self.newPreset[0]}.png').convert('RGBA')
        card = Image.open(f'assets/img/general/profile/base/{self.newPreset[1]}.png').convert('RGBA')
        nametag = Image.open(f'assets/img/general/profile/nametag/{self.newPreset[2]}.png').convert('RGBA')
        
        embed = hikari.Embed(title=f'Customization Preview', color=get_setting('general', 'embed_color'))
        embed.set_image(await self.profile.draw_card(bg, card, nametag))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    async def view_check(self, ctx: ViewContext) -> bool:
        return ctx.user.id == self.inventory.user.id

@plugin.command
@lightbulb.option('nametag', 'The nametag is a label that users can customize to reflect their individual identity.', type=str, autocomplete=True, required=True)
@lightbulb.option('base', 'The base section is where users make fundamental changes to their profile.', type=str, autocomplete=True, required=True)
@lightbulb.option('banner', 'The banner is the top section of the profile and often serves as a visually appealing header.', type=str, autocomplete=True, required=True)
@lightbulb.command('customize', 'Customize your profile!', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def customize(ctx: lightbulb.Context, banner: str, base: str, nametag: str) -> None:
    inventory = Inventory(ctx.member)
    profile = Card(ctx.member)
    
    oldPreset = inventory.get_active_customs()
    activePreset = [banner, base, nametag]
    
    view = ProfileCustomizeView(inventory, profile, activePreset)
    
    for item in activePreset:
        strItem = item.split('-')
        if len(strItem) != 2:
            embed = hikari.Embed(description=f'This is not a valid item!', color=(get_setting('general', 'embed_error_color')))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        elif strItem[0] != 'default' and inventory.get_profile_item(strItem) == False:
            embed = hikari.Embed(description=f'You do not own this {strItem[1]}!', color=(get_setting('general', 'embed_error_color')))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    
    oldPreset = [f'- {item.title().replace("_", " ").split("-")[0]} ({item.split("-")[1]})' for i, item in enumerate(oldPreset)]
    activePreset = [f'- {item.title().replace("_", " ").split("-")[0]} ({item.split("-")[1]})' for i, item in enumerate(activePreset)]
    
    embed = (hikari.Embed(title='Are you sure you want to make changes?', color=get_setting('general', 'embed_color'))
        .add_field('Old Profile', '\n'.join(oldPreset), inline=True)
        .add_field('New Profile', '\n'.join(activePreset), inline=True)
        .set_footer(text='This action cannot be undone.')
    )

    message = await ctx.respond(embed, components=view.build(), flags=hikari.MessageFlag.EPHEMERAL)
    await view.start(message)

@customize.autocomplete('banner', 'base', 'nametag')
async def search_autocomplete(opt: hikari.AutocompleteInteractionOption, ctx: hikari.AutocompleteInteraction):
    inventory = Inventory(ctx.member)
    items = inventory.get_inventory(opt.name)
    items = [(None, 'default', opt.name, '0')] + items
    if len(opt.value) > 0:
        filtered_matches = [hikari.impl.AutocompleteChoiceBuilder(str(item[1]).replace('_', ' ').title(), f'{item[1]}-{item[2]}') for item in items if str(item[1]).lower().startswith(opt.value.lower())]
        return filtered_matches[:10]
    else:
        return [hikari.impl.AutocompleteChoiceBuilder(str(item[1]).replace('_', ' ').title(), f'{item[1]}-{item[2]}') for item in items][:10]

def load(bot):
    bot.add_plugin(plugin)