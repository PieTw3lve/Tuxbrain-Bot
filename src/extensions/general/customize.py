import asyncio
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

loader = lightbulb.Loader()

class CustomizeMenu(lightbulb.components.Menu):
    def __init__(self, inventory: Inventory, profile: Card, newPreset: list) -> None:
        self.saveButton = self.add_interactive_button(style=hikari.ButtonStyle.SUCCESS, emoji="🖨️", label="Save", on_press=self.on_save)
        self.closeButton = self.add_interactive_button(style=hikari.ButtonStyle.DANGER, emoji="✖️", label="Cancel", on_press=self.on_cancel)
        self.previewButton = self.add_interactive_button(style=hikari.ButtonStyle.PRIMARY, emoji="🔍", label="Preview", on_press=self.on_preview)
        self.db = sqlite3.connect(get_setting("general", "database_data_dir"))
        self.cursor = self.db.cursor()
        self.inventory = inventory
        self.profile = profile
        self.newPreset = newPreset

    async def on_save(self, ctx: lightbulb.components.MenuContext) -> None:
        self.cursor.execute("UPDATE profile SET active = 0 WHERE user_id = ?", (ctx.user.id,))
        for item in self.newPreset:
            name, type = str(item).split("-")
            self.cursor.execute("UPDATE profile SET active = 1 WHERE user_id = ? AND name = ? AND type = ?", (ctx.user.id, name, type))
        self.db.commit()

        embed = hikari.Embed(description="Profile has been saved!", color=get_setting("general", "embed_success_color"))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        ctx.stop_interacting()

    async def on_cancel(self, ctx: lightbulb.components.MenuContext) -> None:
        await ctx.interaction.edit_initial_response(components=[])
        ctx.stop_interacting()

    async def on_preview(self, ctx: lightbulb.components.MenuContext) -> None:
        bg = Image.open(f"assets/img/general/profile/banner/{self.newPreset[0]}.png").convert("RGBA")
        card = Image.open(f"assets/img/general/profile/base/{self.newPreset[1]}.png").convert("RGBA")
        nametag = Image.open(f"assets/img/general/profile/nametag/{self.newPreset[2]}.png").convert("RGBA")
        
        embed = hikari.Embed(title=f"Customization Preview", color=get_setting("general", "embed_color"))
        embed.set_image(await self.profile.draw_card(bg, card, nametag))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    async def predicate(self, ctx: lightbulb.components.MenuContext) -> bool:
        return ctx.user.id == self.inventory.user.id

async def item_autocomplete(ctx: lightbulb.AutocompleteContext[str]):
    name = ctx.focused.name
    value = ctx.focused.value
    inventory = Inventory(ctx.interaction.member)
    items = inventory.get_inventory(name)
    items = [(None, "default", name, "0")] + items
    if len(value) > 0:
        filtered_matches = [hikari.impl.AutocompleteChoiceBuilder(str(item[1]).replace("_", " ").title(), f"{item[1]}-{item[2]}") for item in items if str(item[1]).lower().startswith(name.lower())]
        await ctx.respond(filtered_matches[:10])
    else:
        await ctx.respond([hikari.impl.AutocompleteChoiceBuilder(str(item[1]).replace("_", " ").title(), f"{item[1]}-{item[2]}") for item in items][:10])

@loader.command
class Customize(lightbulb.SlashCommand, name="customize", description="Customize your profile!"):
    banner: str = lightbulb.string("banner", "The banner is the top section of the profile and often serves as a visually appealing header.", autocomplete=item_autocomplete)
    base: str = lightbulb.string("base", "The base section is where users make fundamental changes to their profile.", autocomplete=item_autocomplete)
    nametag: str = lightbulb.string("nametag", "The nametag is a label that users can customize to reflect their individual identity.", autocomplete=item_autocomplete)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        inventory = Inventory(ctx.member)
        profile = Card(ctx.member, ctx)
        
        oldPreset = inventory.get_active_customs()
        activePreset = [self.banner, self.base, self.nametag]
        
        menu = CustomizeMenu(inventory, profile, activePreset)
        
        for item in activePreset:
            strItem = item.split("-")
            if len(strItem) != 2:
                embed = hikari.Embed(description=f"This is not a valid item!", color=(get_setting("general", "embed_error_color")))
                return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            elif strItem[0] != "default" and inventory.get_profile_item(strItem) == False:
                embed = hikari.Embed(description=f"You do not own this {strItem[1]}!", color=(get_setting("general", "embed_error_color")))
                return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        oldPreset = [f"- {item.title().replace('_', ' ').split('-')[0]} ({item.split('-')[1]})" for i, item in enumerate(oldPreset)]
        activePreset = [f"- {item.title().replace('_', ' ').split('-')[0]} ({item.split('-')[1]})" for i, item in enumerate(activePreset)]
        
        embed = (hikari.Embed(title="Are you sure you want to make changes?", color=get_setting("general", "embed_color"))
            .add_field("Old Profile", "\n".join(oldPreset), inline=True)
            .add_field("New Profile", "\n".join(activePreset), inline=True)
            .set_footer(text="This action cannot be undone.")
        )

        resp = await ctx.respond(embed, components=menu, flags=hikari.MessageFlag.EPHEMERAL)

        try:
            await menu.attach(ctx.client, timeout=60)
        except asyncio.TimeoutError:
            await ctx.edit_response(resp, components=[])