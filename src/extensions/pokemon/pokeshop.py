import hikari
import lightbulb
import miru

from bot import get_setting, verify_user, register_user
from utils.economy.manager import EconomyManager
from utils.pokemon.pack import StandardPokemonCardPack, PremiumPokemonCardPack

plugin = lightbulb.Plugin('Pokeshop')
economy = EconomyManager()

class PackShop(miru.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)
    
    @miru.button(label='Standard Pack', emoji='<:standard_booster_pack:1073771426324156428>', style=hikari.ButtonStyle.PRIMARY, custom_id='standard_pack_button')
    async def standard(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if verify_user(ctx.user) == None: # if user has never been register
            register_user(ctx.user)

        if economy.remove_money(ctx.user.id, 200, True) == False: # checks if user has enough money
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return

        pack = StandardPokemonCardPack(ctx.user, ctx)
        await pack.buy()
    
    @miru.button(label='Premium Pack', emoji='<:premium_booster_pack:1073771425095237662>', style=hikari.ButtonStyle.PRIMARY, custom_id='premium_pack_button')
    async def premium(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if verify_user(ctx.user) == None: # if user has never been register
            register_user(ctx.user)
        
        if economy.remove_ticket(ctx.user.id, 1) == False: # checks if user has enough tickets
            embed = hikari.Embed(description='You do not have enough tickets!', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        pack = PremiumPokemonCardPack(ctx.user, ctx)
        await pack.buy()

    @miru.button(label='What are Booster Packs?', emoji='❔', style=hikari.ButtonStyle.SECONDARY, custom_id='card_pack_info')
    async def info(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        embed = hikari.Embed(title='What are Booster Packs?', description="Pokémon Booster Packs are packs of 7 randomly selected Pokémon cards, up to Gen 2, that enhance your Pokémon card collection. They include rare cards ranging from 1-5 ⭐, with a chance of finding a shiny Pokémon. You can purchase the standard booster packs using PokéCoins, and premium booster packs require 1 🎟️. Collect and trade cards with other players to build an impressive collection of Gen 2 and earlier Pokémon cards. Perfect for beginners and seasoned collectors alike.", color=get_setting('general', 'embed_color'))
        embed.set_thumbnail('assets/img/pokemon/shop_icon.png')
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('pokeshop', 'Access the PokéShop menu.')
@lightbulb.implements(lightbulb.SlashCommand)
async def shop(ctx: lightbulb.Context) -> None:
    embed = hikari.Embed(title='Welcome to the PokéShop!', description='Get your hands on the newest Pokémon cards at the Pokémon Booster Pack Shop! Simply choose from one of the two options below to start building your collection today. \n\nA standard booster pack costs 🪙 200, while the premium booster pack, which offers a **3x boost** on the chance of getting rare quality cards, can be yours for just 1 🎟️.', color=get_setting('general', 'embed_color'))
    embed.set_thumbnail('assets/img/pokemon/shop_icon.png')

    view = PackShop()
    await ctx.respond(embed, components=view.build())

    client = ctx.bot.d.get('client')
    client.start_view(view)
    
def load(bot):
    bot.add_plugin(plugin)