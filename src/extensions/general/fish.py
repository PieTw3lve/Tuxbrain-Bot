import hikari
import hikari.emojis
import lightbulb
import miru
import random

from lightbulb.ext import tasks
from lightbulb.ext.tasks import CronTrigger
from miru.abc.item import InteractiveViewItem

from utils.economy.manager import EconomyManager
from utils.fishing.bait import Bait
from utils.fishing.config_loader import FishingConfigLoader
from utils.fishing.fish import Fish
from utils.fishing.inventory import Inventory
from utils.fishing.location import Location
from utils.general.config import get_setting

plugin = lightbulb.Plugin('Fish')

economy = EconomyManager()
data = FishingConfigLoader()
todaysWeather = None

@tasks.task(CronTrigger('0 0 * * *'), auto_start=True)
async def update_weather() -> None:
    global todaysWeather
    weathers = list(data.weathers.values())
    weights = [weather.weight for weather in weathers]
    todaysWeather = random.choices(weathers, weights=weights, k=1)[0]

@plugin.listener(hikari.StartedEvent)
async def on_start(event: hikari.StartedEvent) -> None:
    await update_weather()

class FishMenuView(miru.View):
    def __init__(self, author: hikari.User, inventory: Inventory, location: Location,) -> None:
        super().__init__(timeout=300)
        self.inventory = inventory
        self.author = author
        self.location = location
        self.add_item(
            miru.TextSelect(
                custom_id='bait_select',
                placeholder='Select a Bait',
                options=[
                    miru.SelectOption(
                        label=f'{bait.name} ({self.inventory.get_bait_amount(bait)}x)',
                        description=bait.tooltip,
                        emoji=bait.emoji,
                        value=bait.id
                    ) for bait in sorted(self.inventory.get_baits(), key=lambda bait: (bait.success_rate_bonus, bait.quantity_bonus, bait.rarity_bonus), reverse=True)
                ]
            )
        )
        # self.location.print_fish_percentages(self.location.rarity_bonus + todaysWeather.rarity_bonus)
    
    async def _handle_callback(self, item: InteractiveViewItem, ctx: miru.ViewContext) -> None:
        bait = data.baits[ctx.interaction.values[0]]

        if self.inventory.get_bait_amount(bait) == 0:
            embed = hikari.Embed(
                description='You do not have enough bait to fish with that!',
                color=get_setting('general', 'embed_error_color')
            )
            return await ctx.respond(embed=embed, flags=hikari.MessageFlag.EPHEMERAL)

        fish = self.location.get_fish(bait, todaysWeather)
        self.inventory.update_bait(bait, self.inventory.get_bait_amount(bait) - 1)

        if self.inventory.get_bait_amount(bait) == 0:
            self.inventory.delete_bait(bait)

        if fish is None:
            embed = hikari.Embed(
                title='Oh no! The fish got away!',
                description='You left empty-handed this time. Better luck next time!',
                color=get_setting('general', 'embed_error_color')
            )
            return await ctx.edit_response(embed=embed, components=[], flags=hikari.MessageFlag.EPHEMERAL)

        self.stop()
        view = FishCaughtView(ctx.author, self.inventory, bait, self.location, fish)
        await ctx.edit_response(embed=view.embed, components=view.build())
        self.client.start_view(view)
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.author.id

class FishCaughtView(miru.View):
    def __init__(self, author: hikari.User, inventory: Inventory, bait: Bait, location: Location, fish: Fish) -> None:
        super().__init__(timeout=300)
        self.author = author
        self.inventory = inventory
        self.location = location
        self.fish = fish
        self.quantity = fish.get_fish_quantity(bait.quantity_bonus + todaysWeather.quantity_bonus + location.quantity_bonus)
        self.salvageDrops = fish.combine_salvages(self.quantity, randomize=True)
        self.embed = self.get_message()
        self.add_buttons()

    async def _handle_callback(self, item: InteractiveViewItem, ctx: miru.ViewContext) -> None:
        option = ctx.interaction.custom_id

        match option:
            case 'sell_button':
                economy.add_money(ctx.user.id, self.fish.price * self.quantity, True)
                embed = hikari.Embed(
                    title='Money Received!',
                    description=f'You sold **{self.fish.emoji} {self.fish.name} ({self.quantity}x)** for 🪙 {self.fish.price * self.quantity}.',
                    color=get_setting('general', 'embed_success_color')
                )
                await ctx.edit_response(components=[])
                return await ctx.respond(embed=embed)
            case 'salvage_button':
                embed = hikari.Embed(color=get_setting('general', 'embed_color'))
                if self.salvageDrops == []:
                    embed.title = 'Salvage Results'
                    embed.description = f'You did not receive any salvage drops from **{self.fish.emoji} {self.fish.name}**.'
                    flags = hikari.MessageFlag.EPHEMERAL
                elif len(self.inventory.get_baits()) > (25 - len(self.salvageDrops)):
                    embed.title = 'Salvage Failed!'
                    embed.description = f'You do not have enough space in your inventory to salvage **{self.fish.emoji} {self.fish.name}**.'
                    flags = hikari.MessageFlag.EPHEMERAL
                else:
                    for bait, amount in self.salvageDrops:
                        self.inventory.update_bait(bait, self.inventory.get_bait_amount(bait) + amount)

                    baits = [
                        f'> **{bait.emoji} {bait.name} ({amount}x)**\n'
                        f'> -# {bait.description}\n'
                        for bait, amount in self.salvageDrops
                    ]

                    embed.title = 'Salvage Successful!'
                    embed.description = (
                        f'You salvaged **{self.fish.emoji} {self.fish.name}** and received the following items:\n\n'
                        f'{str.format("".join(baits))}\n'
                        '-# Your salvage drops have been added to your inventory.'
                    )
                    embed.color = get_setting('general', 'embed_success_color')
                    flags = hikari.MessageFlag.NONE
                await ctx.edit_response(components=[])
                return await ctx.respond(embed=embed, flags=flags)
            case 'info_button':
                baits = [
                    f'> **{bait.emoji} {bait.name} ({amount}x)**\n'
                    f'>   ⤷ {bait.tooltip}'
                    for bait, amount in self.salvageDrops
                ]

                embed = hikari.Embed(
                    title='Salvage Information',
                    description=(
                        f'**{self.fish.emoji} {self.fish.name}** can be salvaged into the following items:\n\n'
                        f'{str.format("".join(baits))}\n'
                        '‎'
                    ),
                    color=get_setting('general', 'embed_color')
                )
                embed.set_thumbnail(hikari.emojis.Emoji.parse(self.fish.emoji).url)
                return await ctx.respond(embed=embed, flags=hikari.MessageFlag.EPHEMERAL)

    def get_message(self) -> hikari.Embed:
        embed = hikari.Embed(
            title=f'Hooray! You caught a fish!',
            description=(
                f'I caught a **{self.fish.emoji} {self.fish.name}**! {self.fish.description}\n\n'
                f'> **Quantity**: {self.fish.emoji} {self.quantity}x\n'
                f'> **Sell Price**: 🪙 {self.fish.price * self.quantity}\n'
                f'> **Salvage Drops**: {", ".join(f"{bait.emoji} {bait.name} ({amount}x)" for bait, amount in self.salvageDrops)}\n\n'
                '-# What would you like to do with it?'
            ),
            color=get_setting('general', 'embed_color')
        )
        embed.set_thumbnail(hikari.emojis.Emoji.parse(self.fish.emoji).url)
        return embed
    
    def add_buttons(self) -> None:
        self.add_item(
            miru.Button(
                custom_id='sell_button',
                label='Sell',
                emoji='🪙',
                style=hikari.ButtonStyle.PRIMARY
            )
        )
        self.add_item(
            miru.Button(
                custom_id='salvage_button',
                label=f'Salvage',
                emoji='♻️',
                style=hikari.ButtonStyle.DANGER
            )
        )
        self.add_item(
            miru.Button(
                custom_id='info_button',
                emoji='❔',
                style=hikari.ButtonStyle.SECONDARY
            )
        )
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.author.id

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('location', 'The location to fish at.', choices=[location.name for location in data.locations.values()])
@lightbulb.command('fish', 'Catch a fish.')
@lightbulb.implements(lightbulb.SlashCommand)
async def fish(ctx: lightbulb.Context) -> None:
    inventory = Inventory(ctx.author)

    if inventory.get_baits() == []:
        embed = hikari.Embed(
            description="You're out of bait! Head over to `/shop` to purchase some to continue fishing.",
            color=get_setting('general', 'embed_error_color')
        )
        return await ctx.respond(embed=embed, flags=hikari.MessageFlag.EPHEMERAL)

    for locationItem in data.locations.values():
        if locationItem.name == ctx.options['location']:
            location = locationItem
    
    sortedFish = sorted(location.fish, key=lambda fish: (fish.weight, -fish.price), reverse=True)

    embed = hikari.Embed(
        title=f'Fishing at {location.name}',
        description=(
            f'{location.description} '
            f'{todaysWeather.description}\n\n'
            f'> **Weather**: {todaysWeather.emoji} {todaysWeather.name}\n'
            f'> **Catch Bonus**: `{todaysWeather.success_rate_bonus * 100:.0f}%`\n'
            f'> **Quantity Bonus**: `{todaysWeather.quantity_bonus * 100:.0f}%`\n'
            f'> **Rarity Bonus**: `{todaysWeather.rarity_bonus * 100:.0f}%`\n'
            f'‎'
        ),
        color=get_setting('general', 'embed_color')
    )

    embed.add_field(
        name='Available Fish',
        value='\n'.join(f'{fish.emoji} {fish.name}' for fish in sortedFish) or 'N/A',
        inline=True
    )
    embed.add_field(
        name='Sell Price',
        value='\n'.join(f'🪙 {fish.price}' for fish in sortedFish) or 'N/A',
        inline=True
    )
    embed.add_field(
        name='Rarity',
        value='\n'.join(f'{location.get_fish_rarity(fish, todaysWeather)}' for fish in sortedFish) or 'N/A',
        inline=True
    )
    embed.set_thumbnail(hikari.emojis.Emoji.parse(location.emoji).url)

    view = FishMenuView(ctx.author, inventory, location)
    await ctx.respond(embed, components=view.build())
    client = ctx.bot.d.get('client')
    client.start_view(view)

def load(bot):
    bot.add_plugin(plugin)