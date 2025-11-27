import hikari
import lightbulb

from PIL import Image

from bot import get_setting
from utils.profile.inventory import Inventory
from utils.profile.card import Card

loader = lightbulb.Loader()

@loader.command
class Profile(lightbulb.SlashCommand, name="profile", description="Retrieve information about yourself or a Discord member."):
    user: hikari.User = lightbulb.user("user", "The user to get information about.", default=None)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        user = self.user or ctx.member
    
        if not user:
            embed = hikari.Embed(description="That user is not in the server.", color=get_setting("general", "embed_error_color"))
            await ctx.respond(embed)
            return

        inventory = Inventory(user)
        profile = Card(user, ctx)

        bg, card, nametag = inventory.get_active_customs()
        bg = Image.open(f"assets/img/general/profile/banner/{bg}.png").convert("RGBA")
        card = Image.open(f"assets/img/general/profile/base/{card}.png").convert("RGBA")
        nametag = Image.open(f"assets/img/general/profile/nametag/{nametag}.png").convert("RGBA")

        await ctx.respond(attachment=await profile.draw_card(bg, card, nametag))