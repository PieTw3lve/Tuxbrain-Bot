import hikari
import lightbulb
import random

from datetime import datetime, timedelta

from bot import get_setting, verify_user, register_user
from utils.daily.manager import DailyManager
from utils.daily.events.chest import DailyChestsView
from utils.daily.events.mystery_box import DailyMysteryBoxView
from utils.daily.events.fox import DailyFoxView

plugin = lightbulb.Plugin('Daily')

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('daily', 'Claim your daily reward!')
@lightbulb.implements(lightbulb.SlashCommand)
async def daily(ctx: lightbulb.Context) -> None:
    if verify_user(ctx.author) == None: # if user has never been register
        register_user(ctx.author)
    
    dailyManager = DailyManager(ctx.author)

    if dailyManager.on_cooldown() == True:
        embed = hikari.Embed(description='You already claimed your daily today!', color=get_setting('general', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    dailyManager.update_streak()
    scenarioList = ([1, 2, 3], [80, 10, 5])
    scenario = random.choices(scenarioList[0], scenarioList[1])[0]
    
    match scenario:
        case 1: # The Choice of Chests
            embed = hikari.Embed(title=f'The Choice of Chests: Unveiling Your Fate', description="In a dimly lit chamber, three chests await your selection, each with a predetermined sum of coins inside. Your decision will unveil not just wealth, but a reflection of your desires and your readiness for life's uncertainties. Choose wisely, for destiny awaits.", color=get_setting('general', 'embed_color'), timestamp=datetime.now().astimezone())
            embed.set_thumbnail('assets/img/general/dailies/treasure_chest.png')
            embed.add_field(name='<:small_chest:1143255749322100837> - Old Chest', value='This weathered and timeworn chest may hold a hidden treasure of unknown worth, offering an element of mystery and nostalgia.')
            embed.add_field(name='<:medium_chest:1143258292253118525> - Standard Chest', value='The middle-of-the-road option, this chest offers a reliable chance at a decent haul of coins, without any frills or extravagance.')
            embed.add_field(name='<:large_chest:1143260812002218164> - Luxurious Chest', value='The epitome of opulence, this chest tends to promise high-value rewards, making it the grandest and most alluring choice among the three.')
            embed.set_footer(text=f'Requested by {ctx.author.global_name}', icon=ctx.author.display_avatar_url)
            view = DailyChestsView(dailyManager, ctx.author)
        case 2: # The Mystery Box
            embed = hikari.Embed(title=f'The Mystery Box: A Decision to Share or Snare', description="Before you lies an enigmatic mystery box, an object shrouded in intrigue and uncertainty. Its exterior, adorned with intricate patterns, beckons you to uncover its secrets. However, this box comes with a twist: it holds the power to either reward your generosity or ensnare your curiosity.", color=get_setting('general', 'embed_color'), timestamp=datetime.now().astimezone())
            embed.set_thumbnail('assets/img/general/dailies/question_mark.png')
            embed.add_field(name='The Gift of Connection', value='If you choose to share this mysterious box with another soul, a remarkable surprise awaits. Inside, you will find not just a reward for your generosity, but a token of camaraderie and connection. Perhaps a heartwarming message or a gesture of goodwill that can forge a bond between you and your chosen companion.')
            embed.add_field(name='The Solitary Treasure', value="If you opt to open the box for yourself, a grand reward might also await. It could be a treasure beyond your wildest dreams or a revelation that changes your life's course. The enigma rewards those who trust in their instincts and tread their path alone.")
            embed.set_footer(text=f'Requested by {ctx.author.global_name}', icon=ctx.author.display_avatar_url)
            view = DailyMysteryBoxView(dailyManager, ctx.author)
        case 3: # Enchanted Encounter
            embed = hikari.Embed(title=f'Enchanted Encounter: A Choice in the Wilderness', description="As you wander along a serene forest trail, the dappled sunlight filtering through the thick canopy overhead, you suddenly stumble upon an unexpected sight. There, nestled among the ferns and moss-covered rocks, is a small, curious creature. It's a red fox, its fiery fur contrasting beautifully with the lush greenery of the forest.", color=get_setting('general', 'embed_color'), timestamp=datetime.now().astimezone())
            embed.set_thumbnail('assets/img/general/dailies/fox.png')
            embed.add_field(name=':palm_down_hand: - PET THE GOD DAMN FOX', value="You're overwhelmed by an irresistible urge. You simply must pet the fox, no questions asked. It's as if the universe itself conspires for you to pet that fox at this very moment.")
            embed.add_field(name='<:sleeping_fox:1143665534030848080> - Leave the Fox Alone', value="Let the fox rest peacefully and continue with your day.")
            embed.set_footer(text=f'Requested by {ctx.author.global_name}', icon=ctx.author.display_avatar_url)
            view = DailyFoxView(dailyManager, ctx.author)
    
    await ctx.respond(embed, components=view.build())
    client = ctx.bot.d.get('client')
    client.start_view(view)

def load(bot):
    bot.add_plugin(plugin)