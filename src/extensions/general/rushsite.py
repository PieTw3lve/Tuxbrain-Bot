import os
import hikari
import lightbulb
import sqlite3
import re

from lightbulb.ext import tasks
from datetime import datetime
from collections import defaultdict

from bot import get_setting

plugin = lightbulb.Plugin('Rushsite')
dataDirectory = 'database/rushsite'
trophiesIndex = {'s1': '<:TrophyS1:1143265272510304308>', 's2': '<:TrophyS2:1143265277925142578>', 's3': '<:TrophyS3:1143265282614366258>', 's4': '<:TrophyS4:1143265285848178778>', 's5': '<:TrophyS5:1143272567965237360>',}
rushsiteStats = {}
allNames = []

@tasks.task(d=1, auto_start=True)
async def update_rushsite_data():
    global rushsiteStats, allNames
    teamStats = defaultdict(lambda: defaultdict(int))
    playerStats = defaultdict(lambda: defaultdict(int))
    playerTeams = defaultdict(list)
    mostCommonMaps = defaultdict(lambda: defaultdict(int))
    mostCommonSide = defaultdict(lambda: defaultdict(int))
    validValueCount = defaultdict(lambda: defaultdict(int))
    teamTrophyWins = defaultdict(list)
    playerTrophyWins = defaultdict(list)

    sqlite_files = [filename for filename in os.listdir(dataDirectory) if filename.endswith('.sqlite')]

    def custom_sort(filename):
        return int(filename.split('_s')[1].split('.sqlite')[0])
    
    sorted_sqlite_files = sorted(sqlite_files, key=custom_sort)

    for filename in sorted_sqlite_files:
        if filename.endswith('.sqlite'):
            path = os.path.join(dataDirectory, filename)
            conn = sqlite3.connect(path)
            cursor = conn.cursor()

            # Calculate team stats
            cursor.execute('SELECT * FROM Team_Stats')
            db = cursor.fetchall()
            for team in db:
                teamName = team[0]
                teamAddLabels = ['Wins', 'Draws', 'Losses', 'Maps_Played']
                # Update additive team statistics
                for index, stat in enumerate(team[1:5], start=1):
                    teamStats[teamName][teamAddLabels[index-1]] += stat if stat is not None else 0
                # Update the mean team statistics
                if team[5] is not None:
                    teamStats[teamName]['Group_Points'] += team[5]
                    validValueCount[teamName]['Group_Points'] += 1
                else:
                    teamStats[teamName]['Group_Points'] += 0
                if team[6] is not None:
                    teamStats[teamName]['Group_Placings'] += team[6]
                    validValueCount[teamName]['Group_Placings'] += 1
                else:
                    teamStats[teamName]['Group_Placings'] += 0
                if team[7] is not None:
                    teamStats[teamName]['Final_Placing'] += team[7]
                    validValueCount[teamName]['Final_Placing'] += 1
                    if team[7] == 1:
                        teamStats[teamName]['Trophies_Won'] += 1
                        teamTrophyWins[teamName].append(filename.replace('rushsite_', '').replace('.sqlite', ''))
                    else:
                        teamStats[teamName]['Trophies_Won'] += 0
                else:
                    teamStats[teamName]['Final_Placing'] += 0
                if team[9] is not None:
                    teamStats[teamName]['T_Side_Win_Rate'] += team[9]
                    validValueCount[teamName]['T_Side_Win_Rate'] += 1
                else:
                    teamStats[teamName]['T_Side_Win_Rate'] += 0
                if team[10] is not None:
                    teamStats[teamName]['CT_Side_Win_Rate'] += team[10]
                    validValueCount[teamName]['CT_Side_Win_Rate'] += 1
                else:
                    teamStats[teamName]['CT_Side_Win_Rate'] += 0
                
                # Count most common starting side
                mostCommonSide[teamName][team[8]] += 1

                # Count most common maps
                maps = team[11].split('/')
                for map in maps:
                    mapName = map.strip()
                    mostCommonMaps[teamName][mapName] += 1

            # Calculate player stats
            cursor.execute('SELECT * FROM Player_Stats')
            db = cursor.fetchall()
            statLabels = ['Wins', 'Draws', 'Losses', 'K', 'A', 'D', 'MVP', 'SCORE', 'UD', 'EF', 'RP', 'DMG', 'HSK', 'Victories']
            for player in db:
                playerName = player[0]
                # playerTeams[playerName].add(player[1])
                playerTeams[playerName].append(player[1])
                
                for index, stat in enumerate(player[2:], start=2):
                    if statLabels[index-2] == 'Victories' and player[15] == 1:
                        playerTrophyWins[playerName].append(filename.replace('rushsite_', '').replace('.sqlite', ''))
                    playerStats[playerName][statLabels[index-2]] += stat if stat is not None else 0
            conn.close()

    # Include player teams in the players dictionary
    for playerName, teams in playerTeams.items():
        teams.reverse()
        teamList = []
        [teamList.append(x) for x in teams if x not in teamList]
        playerStats[playerName]['Teams'] = teamList

    # Calculate averages for team stats
    for teamName in teamStats.keys():
        for key in teamStats[teamName].keys():
            # Only calculate the average for the specified fields
            if key in ['Group_Points', 'Group_Placings', 'Final_Placing', 'T_Side_Win_Rate', 'CT_Side_Win_Rate']:
                if validValueCount[teamName][key] > 0:
                    teamStats[teamName][key] /= validValueCount[teamName][key]
            else:
                teamStats[teamName][key] = int(teamStats[teamName][key])  # Convert other fields to int

        # Get the most common starting side for each team
        maxOccurrenceStartingSide = max(mostCommonSide[teamName].values())
        mostCommonSideOptions = [
            side for side, occurrence in mostCommonSide[teamName].items() if occurrence == maxOccurrenceStartingSide
        ]
        teamStats[teamName]['Most_Common_Starting_Side'] = mostCommonSideOptions

        # Get the most common map for each team
        maxOccurrence = max(mostCommonMaps[teamName].values())
        most_common_map = [
            map_name for map_name, occurrence in mostCommonMaps[teamName].items() if occurrence == maxOccurrence
        ]
        teamStats[teamName]['Most_Common_Map'] = most_common_map if most_common_map else ''

    rushsiteStats = {'Teams': dict(teamStats), 'Players': dict(playerStats), 'Team_Trophy_Wins': teamTrophyWins, 'Player_Trophy_Wins': playerTrophyWins}
    allNames = (list(rushsiteStats['Teams'].keys()), list(rushsiteStats['Players'].keys()))

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('rushsite', 'Explore Rushsite statistics and information.')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def rushsite(ctx: lightbulb.Context) -> None:
    return

## Overview Command ##

@rushsite.child
@lightbulb.option('season', 'The name of the stat.', type=str, choices=['Season 1', 'Season 2', 'Season 3'], required=True)
@lightbulb.command('overview', 'Get an overview of a specific season.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def overview(ctx: lightbulb.Context, season: str) -> None:
    embed = hikari.Embed(title=f'{season} Overview', color=get_setting('settings', 'embed_color'), timestamp=datetime.now().astimezone())
    embed.set_image(f'assets/img/rushsite/overviews/{season.lower().replace(" ", "_")}.png')
    embed.set_footer(text=f'Requested by {ctx.author.global_name}', icon=ctx.author.display_avatar_url)
    await ctx.respond(embed)

## SignUp Command ##

@rushsite.child
@lightbulb.command('info', 'Get info for the latest Rushsite tournament!', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def signup(ctx: lightbulb.Context) -> None:
    embed = hikari.Embed(title='Rushsite Tournament Information', description=f"Rushsite is a seasonal CS:GO 2v2 wingman competition. Six teams or more fight through group stages and playoff brackets to become champion!", color=get_setting('settings', 'embed_color'))
    embed.set_thumbnail('assets/img/rushsite/logos/placeholder.png')
    embed.add_field(name='Game', value='Counter-Strike 2', inline=True)
    embed.add_field(name='Current Season', value='Season 4', inline=True)
    embed.add_field(name='Map Pool', value='N/A', inline=True)
    embed.add_field(name='Prize Pool', value='$100', inline=True)
    embed.add_field(name='Start Date', value='October 20th', inline=True)
    embed.add_field(name='End Date', value='October 22th', inline=True)
    embed.add_field(name='Where can I sign up?', value='The tournament is open and any team can register. Sign up by private messaging <@265992381780721675>.', inline=False)
    embed.add_field(name='Where can I watch?', value="Don't miss the action, as the tournament will be streamed live on [Twitch](https://twitch.tv/ryqb)!", inline=False)
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

## Search Command ##

@rushsite.child
@lightbulb.option('name', 'The name of the player or team.', type=str, autocomplete=True, required=True)
@lightbulb.command('search', 'Get info about this player or team.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def search(ctx: lightbulb.Context, name: str) -> None:
    if name not in allNames[0] + allNames[1]: # If name is not in teams or players
        embed = (hikari.Embed(description=f'The player or team name cannot be found.', color=get_setting('settings', 'embed_error_color')))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif name in allNames[0]: # If name is a team
        teamName = allNames[0][allNames[0].index(name)]
        trophies = []

        for trophy in rushsiteStats['Team_Trophy_Wins'][teamName]:
            trophies.append(trophiesIndex.get(trophy))

        try:
            wins, draws, losses, mapsPlayed, avgGroupPoints, avgGroupPlacing, avgFinalPlacing, victories, tWinRate, ctWinRate, commonSide, commonMap = rushsiteStats['Teams'][teamName].values()
        except ValueError:
            wins, draws, losses, mapsPlayed, avgGroupPoints, avgGroupPlacing, avgFinalPlacing, victories, commonSide, commonMap = rushsiteStats['Teams'][teamName].values()
            tWinRate = None
            ctWinRate = None
        if commonSide == ['Even']:
            commonSide = ['CT', 'T']
        
        img = re.sub(r'[^a-zA-Z0-9\s]', '', str(teamName).lower().replace(" ", ""))
        thumbnail = f'assets/img/rushsite/logos/{img}.png'
        embed = (hikari.Embed(title=f'Team: {teamName} {" ".join(trophies)}', color=get_setting('settings', 'embed_color'), timestamp=datetime.now().astimezone()))
        embed.set_thumbnail(thumbnail if os.path.exists(thumbnail) else 'assets/img/rushsite/logos/placeholder.png')
        embed.add_field(name='Favorite Maps', value=f'> {f"{chr(10)}> ".join(commonMap)}', inline=True)
        embed.add_field(name='Avg. Group Placings', value=f'> {add_ordinal_suffix(avgGroupPlacing)}', inline=True)
        embed.add_field(name='Avg. Final Placings', value=f'> {add_ordinal_suffix(avgFinalPlacing)}', inline=True)
        embed.add_field(name='Top Pick', value=f'> {", ".join(commonSide)}', inline=True)
        embed.add_field(name='Terrorist WR', value=f'> {int(tWinRate*100+0.5):,}%', inline=True)
        embed.add_field(name='C-Terrorist WR', value=f'> {int(ctWinRate*100+0.5):,}%', inline=True)
        embed.add_field(name=f'Tournament Maps Won ({wins}/{mapsPlayed})', value=printProgressBar(iteration=wins, total=mapsPlayed, prefix='', suffix = '', length = 18), inline=False)
        embed.set_footer(text=f'Requested by {ctx.author.global_name}', icon=ctx.author.display_avatar_url)
        await ctx.respond(embed)
    else: # If name is a player
        playerName = allNames[1][allNames[1].index(name)]
        wins, draws, losses, kills, assists, deaths, mvp, score, ud, ef, rp, dmg, hsk, victories, teams = rushsiteStats['Players'][playerName].values()
        thumbnail = f'assets/img/rushsite/logos/{str(teams[0]).lower().replace(" ", "")}.png'
        trophies = []

        for trophy in rushsiteStats['Player_Trophy_Wins'][playerName]:
            trophies.append(trophiesIndex.get(trophy))
        
        try:
            kdr = kills/deaths
        except ZeroDivisionError:
            kdr = 0
        
        embed = (hikari.Embed(title=f'Player: {playerName} ({", ".join(teams)}) {" ".join(trophies)}', color=get_setting('settings', 'embed_color'), timestamp=datetime.now().astimezone()))
        embed.set_thumbnail(thumbnail if os.path.exists(thumbnail) else 'assets/img/rushsite/logos/placeholder.png')
        embed.add_field(name='Kills', value=f'> {kills:,}', inline=True)
        embed.add_field(name='Assists', value=f'> {assists:,}', inline=True)
        embed.add_field(name='Deaths', value=f'> {deaths:,}', inline=True)
        embed.add_field(name='KDR', value=f'> {kdr:,.2f}', inline=True)
        embed.add_field(name='MVPs Earned', value=f'> {mvp:,}', inline=True)
        embed.add_field(name='Score Earned', value=f'> {score:,}', inline=True)
        embed.add_field(name='Utility Dmg', value=f'> {ud:,}', inline=True)
        embed.add_field(name='Enemy Flashes', value=f'> {ef:,}', inline=True)
        embed.add_field(name='Damage Dealt', value=f'> {dmg:,}', inline=True)
        embed.add_field(name=f'Tournament Maps Won ({wins}/{wins+draws+losses})', value=printProgressBar(iteration=wins, total=wins+draws+losses, prefix='', suffix = '', length = 18), inline=False) # iter = wins | total = total matches
        embed.add_field(name='Headshot Percentage', value=printProgressBar(iteration=hsk, total=kills, prefix='', suffix = '', length = 18), inline=False)
        embed.set_footer(text=f'Requested by {ctx.author.global_name}', icon=ctx.author.display_avatar_url)
        await ctx.respond(embed)

@search.autocomplete("name")
async def search_autocomplete(opt: hikari.AutocompleteInteractionOption, inter: hikari.AutocompleteInteraction):
    names = allNames[0] + allNames[1]
    filtered_matches = [name for name in names if str(name).lower().startswith(opt.value.lower())]
    return filtered_matches[:10]

def add_ordinal_suffix(number):
    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    if number % 1 == 0.5:
        lower_number = int(number - 0.5)
        upper_number = int(number + 0.5)
    else:
        lower_number = round(number)
        upper_number = lower_number

    lower_suffix = suffixes.get(lower_number % 10, 'th')
    upper_suffix = suffixes.get(upper_number % 10, 'th')

    if lower_suffix == upper_suffix:
        return f"{lower_number}{lower_suffix}"
    else:
        return f"{lower_number}{lower_suffix}-{upper_number}{upper_suffix}"

def printProgressBar (iteration, total, prefix: str, suffix: str, decimals = 1, length = 100, fill = '▰', empty = '▱'):
    try:
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
    except ZeroDivisionError:
        percent = 0
        filledLength = 0
    bar = fill * filledLength + empty * (length - filledLength)
    
    return f'\r{prefix} {bar} {percent}% {suffix}'

## Rank Command ##

@rushsite.child
@lightbulb.option('stat', 'The name of the stat.', type=str, choices=['Wins','Draws','Losses','Kills','Assists','Deaths','MVPs','Score','Damage','Utility Damage','Enemies Flashed','Rounds Played','Headshot Kills','Tournament Victories'], required=True)
@lightbulb.command('rank', 'Get the top 10 players based on chosen stat.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def search(ctx: lightbulb.Context, stat: str) -> None:
    statDict = {'Wins': 'Wins', 'Draws': 'Draws', 'Losses': 'Losses', 'Kills': 'K', 'Assists': 'A', 'Deaths': 'D', 'MVPs': 'MVP', 'Score': 'SCORE', 'Utility Damage': 'UD', 'Enemies Flashed': 'EF', 'Rounds Played': 'RP', 'Damage': 'DMG', 'Headshot Kills': 'HSK', 'Tournament Victories': 'Victories'}
    amount = 10
    
    users, values = get_top_stats(rushsiteStats['Players'], statDict.get(stat), amount)

    embed = hikari.Embed(title=f'Top {amount} players based on {stat}', color=get_setting('settings', 'embed_color'), timestamp=datetime.now().astimezone())
    embed.add_field(name='Players', value='\n'.join(users), inline=True)
    embed.add_field(name=stat, value='\n'.join(values), inline=True)
    embed.set_footer(text=f'Requested by {ctx.author.global_name}', icon=ctx.author.display_avatar_url)
    await ctx.respond(embed)

def get_top_stats(playerStats: dict, statName: str, amount: int) -> list:
    players = sorted(playerStats.items(), key=lambda x: x[1][statName], reverse=True)
    users = []
    values = []
    for i, (player, stats) in enumerate(players[:10], start=1):
        users.append(f'`{i}.` {str(player)}')
        values.append(f'`{str(rushsiteStats["Players"][player][statName])}`')
    return (users, values)

def load(bot):
    bot.add_plugin(plugin)