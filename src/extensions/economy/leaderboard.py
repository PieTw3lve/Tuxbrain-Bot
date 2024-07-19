import hikari
import lightbulb

from .update import getLeaderboard, getLeaderboardLastRefresh
from bot import get_setting

plugin = lightbulb.Plugin('Leaderboard')

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('leaderboard', 'View economy leaderboard rankings.', aliases=['baltop'], pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def baltop(ctx: lightbulb.SlashContext) -> None:
    leaderboardEco = getLeaderboard()
    leaderboardEcoLastRefresh = getLeaderboardLastRefresh()
    rankings = []
    balances = []
    tpasses = []
    
    if len(leaderboardEco) > 0:
        try:
            for i in range(10):
                rankings.append(f'{leaderboardEco[i]["rank"]} <@{leaderboardEco[i]["user_id"]}>')
                balances.append(f'🪙 {leaderboardEco[i]["balance"]:,}')
                tpasses.append(f'🎟️ {leaderboardEco[i]["tpass"]:,}')
        except IndexError:
            pass

        embed = hikari.Embed(title='Economy Leaderboard', color=get_setting('general', 'embed_color'), timestamp=leaderboardEcoLastRefresh)
        embed.add_field(name='Discord User', value='\n'.join(rankings), inline=True)
        embed.add_field(name='Balance', value='\n'.join(balances), inline=True)
        embed.add_field(name='Tux Pass', value='\n'.join(tpasses), inline=True)
        embed.set_footer(f'Last updated')
    else:
        embed = hikari.Embed(title='Economy Leaderboard', color=get_setting('general', 'embed_color'), timestamp=leaderboardEcoLastRefresh)
        embed.add_field(name='Discord User', value='🥇 Unknown', inline=True)
        embed.add_field(name='Balance', value='🪙 0', inline=True)
        embed.add_field(name='Tux Pass', value='🎟️ 0', inline=True)
        embed.set_footer(f'Last updated')
    
    await ctx.respond(embed)

def load(bot):
    bot.add_plugin(plugin)