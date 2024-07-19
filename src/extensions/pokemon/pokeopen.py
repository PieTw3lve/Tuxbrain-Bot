import hikari
import lightbulb

from bot import get_setting
from utils.pokemon.inventory import Inventory
from utils.pokemon.pack import StandardPokemonCardPack, PremiumPokemonCardPack

plugin = lightbulb.Plugin('Pokeopen')

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('uuid', 'Enter a pack ID you want to open.', type=str, required=True)
@lightbulb.command('pokeopen', 'Unbox a Pokémon card pack.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def open(ctx: lightbulb.Context, uuid: str) -> None:
    inventory = Inventory(ctx, ctx.user)
    result = inventory.get_item(uuid)

    if not result:
        embed = hikari.Embed(description='You do not own this pack!', color=get_setting('general', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    else:
        name, item = result

    if name == 'Card':
        embed = hikari.Embed(description='You cannot open a card!', color=get_setting('general', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    packID, user, date, name = item
    
    if inventory.get_inventory_capacity() + get_setting('pokemon', 'pokemon_pack_amount') > inventory.max:
        embed = hikari.Embed(description='You do not have enough inventory space!', color=get_setting('general', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif name == 'Standard':
        pack = StandardPokemonCardPack(ctx.user, ctx)
    else:
        pack = PremiumPokemonCardPack(ctx.user, ctx)
    
    await pack.open(packID)

def load(bot):
    bot.add_plugin(plugin)