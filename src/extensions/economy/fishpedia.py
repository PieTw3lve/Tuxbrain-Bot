import hikari
import hikari.emojis
import lightbulb
import itertools

from extensions.economy.fish import data
from utils.fishing.bait import Bait
from utils.fishing.fish import Fish
from utils.fishing.location import Location
from utils.fishing.weather import Weather
from utils.general.config import get_setting

plugin = lightbulb.Plugin('Fish')

terms = list(itertools.chain(data.baits.values(), data.fishes.values(), data.locations.values(), data.weathers.values()))

class FishpediaTerm:
    def __init__(self, name: str, value: Bait | Fish | Location | Weather):
        self.name = name
        self.value = f'{value.__class__.__name__},{value.id}'
    
    def __str__(self) -> str:
        return self.name

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('term', 'The term to search for.', autocomplete=True, required=True)
@lightbulb.command('fishpedia', 'Get information on anything related to fishing.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def fishpedia(ctx: lightbulb.Context, term: str) -> None:
    termType, termId = term.split(',')
    
    dataMap = {
        'Bait': data.baits,
        'Fish': data.fishes,
        'Location': data.locations,
        'Weather': data.weathers
    }
    
    if termType not in dataMap:
        embed = hikari.Embed(
            description='Invalid term type.',
            color=get_setting('general', 'embed_error_color')
        )
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    
    itemDict = dataMap[termType]
    item = itemDict.get(termId)
    
    if not item:
        embed = hikari.Embed(
            description='Item not found.',
            color=get_setting('general', 'embed_error_color')
        )
        return await ctx.respond("Item not found.", flags=hikari.MessageFlag.EPHEMERAL)
    
    def create_embed(item, fish=False):
        if fish:
            salvage = item.combine_salvages(1, randomize=False)
            description = (
                f'{item.description}\n\n'
                f'> **Price**: 🪙 {item.price}\n'
                f'> **Quantity**: {item.min} - {item.max}\n'
                f'> **Salvage Drops**: {", ".join(f"{bait.emoji} {bait.name} ({count}x)" for bait, count in salvage)}'
            )
        else:
            description = (
                f'{item.description}\n\n'
                f'> **Success Rate Bonus**: `{item.success_rate_bonus * 100:.0f}%`\n'
                f'> **Quantity Bonus**: `{item.quantity_bonus * 100:.0f}%`\n'
                f'> **Rarity Bonus**: `{item.rarity_bonus * 100:.0f}%`'
            )
        
        return hikari.Embed(
            title=f'{item.name}',
            description=description,
            color=get_setting('general', 'embed_color')
        ).set_thumbnail(hikari.emojis.Emoji.parse(item.emoji).url)
    
    embed = create_embed(item, fish=(termType == 'Fish'))
    await ctx.respond(embed)

@fishpedia.autocomplete('term')
async def search_autocomplete(opt: hikari.AutocompleteInteractionOption, inter: hikari.AutocompleteInteraction):
    resultList = []
    for term in terms:
        if term.name.lower().startswith(opt.value.lower()) and len(resultList) < 25:
            option = FishpediaTerm(term.name, term)
            resultList.append(option)
    return resultList

def load(bot):
    bot.add_plugin(plugin)