import os
import typing as t
import hikari
import lightbulb
import miru
import sqlite3

from lightbulb.ext import tasks
from datetime import datetime
from collections import defaultdict
from miru.abc.item import ViewItem
from miru.context import ViewContext

from miru.context.view import ViewContext
from miru.select.text import SelectOption
from bot import get_setting
from .admin import printProgressBar


plugin = lightbulb.Plugin('Rushsite')

dataDirectory = 'database/rushsite'
rushsiteStats = {}
allNames = []

@tasks.task(d=1, auto_start=True)
async def update_rushsite_data():
    global rushsiteStats, allNames
    teamStats = defaultdict(lambda: defaultdict(int))
    playerStats = defaultdict(lambda: defaultdict(int))
    playerTeams = defaultdict(set)
    mostCommonMaps = defaultdict(lambda: defaultdict(int))
    mostCommonSide = defaultdict(lambda: defaultdict(int))
    validValueCount = defaultdict(lambda: defaultdict(int)) # To track the count of valid values for each field

    for filename in os.listdir(dataDirectory):
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
                # Update addative team statistics
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
            statLabels = ['Wins', 'Draws', 'Losses', 'K', 'A', 'D', 'MVP', 'SCORE', 'UD', 'EF', 'RP', 'DMG', 'HSK', 'Trophies']
            for player in db:
                playerName = player[0]
                playerTeams[playerName].add(player[1])
                
                for index, stat in enumerate(player[2:], start=2):
                    playerStats[playerName][statLabels[index-2]] += stat if stat is not None else 0
            conn.close()

    # Include player teams in the players dictionary
    for playerName, teams in playerTeams.items():
        playerStats[playerName]['Teams'] = list(teams)

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

    rushsiteStats = {'Teams': dict(teamStats), 'Players': dict(playerStats)}
    allNames = (list(rushsiteStats['Teams'].keys()), list(rushsiteStats['Players'].keys()))

## Rushsite Subcommand ##

@plugin.command
@lightbulb.command('rushsite', 'Search through Rushsite statistics.')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def rushsite(ctx: lightbulb.Context) -> None:
    return

## Rushsite Strike Command ##

class MapOption(miru.SelectOption):
    def __init__(self, map: str) -> None:
        super().__init__(label=map.capitalize(), value=map.lower())

class MapSelection(miru.TextSelect):
    def __init__(self, options: list) -> None:
        super().__init__(options=options, custom_id='strike_select', placeholder='Eliminate a Map')

class SideSelection(miru.TextSelect):
    def __init__(self) -> None:
        super().__init__(options=[miru.SelectOption(label='Counter-Terrorist', emoji='<:CounterTerrorist:1139266351073079406>', value='ct'), miru.SelectOption(label='Terrorist', emoji='<:Terrorist:1139272220884091001>', value='t')], custom_id='side_select', placeholder='Pick a Side')

class StrikeViewPools(miru.View):
    def __init__(self, embed: hikari.Embed, maps: list, user1: hikari.User, user2: hikari.User) -> None:
        super().__init__(timeout=None, autodefer=True)
        self.embed = embed
        self.maps = maps
        self.user1 = user1
        self.user2 = user2
        self.round = 1

    async def _handle_callback(self, item: ViewItem, ctx: ViewContext,) -> None:
        select = ctx.interaction.values[0]
        
        try:
            self.maps.remove(select.capitalize())
        except ValueError:
            pass

        if len(self.maps) > 1:
            options = list()
            self.remove_item(item)
        
            options = [MapOption(map) for map in self.maps]
            self.add_item(MapSelection(options))

            self.round += 1
            self.update_strike_text(select)
            await ctx.edit_response(self.embed, components=self.build())
        else:
            self.round = 2
            winner = self.maps[0].capitalize()
            if select not in ['t', 'ct']:
                self.remove_item(item)
                self.add_item(SideSelection())
                embed = hikari.Embed(title=f'**{self.user2.global_name}** choose your starting side on {winner}:', color=get_setting('embed_color'))
                embed.set_image(f'assets/img/rushsite/maps/{winner.lower()}.png')
                await ctx.edit_response(embed, components=self.build())
            elif select == 't':
                embed = hikari.Embed(title=f'Strike Results:', description=f'The chosen map is **{winner}**!\n\n{self.user2.global_name} will start on **Terrorist**\n{self.user1.global_name} will start on **Counter-Terrorist**', color=get_setting('embed_color'))
                embed.set_image(f'assets/img/rushsite/maps/{winner.lower()}.png')
                await ctx.edit_response(embed, components=[])
                self.stop()
            else:
                embed = hikari.Embed(title=f'Strike Results:', description=f'The chosen map is **{winner}**!\n\n{self.user2.global_name} will start on **Counter-Terrorist**\n{self.user1.global_name} will start on **Terrorist**', color=get_setting('embed_color'))
                embed.set_image(f'assets/img/rushsite/maps/{winner.lower()}.png')
                await ctx.edit_response(embed, components=[])
                self.stop()

    async def view_check(self, ctx: ViewContext) -> bool:
        if self.round % 2 == 0: # checks if round number is even
            return ctx.user.id == self.user2.id
        else:
            return ctx.user.id == self.user1.id
    
    def update_strike_text(self, map: str) -> None:
        self.embed.title = f'Turn {self.round}: {self.user2.global_name if self.round % 2 == 0 else self.user1.global_name} choose a stage to eliminate!'
        self.embed.description = f'**{map.capitalize()}** was elminated!'
        return

class StrikeViewPlayoffs(miru.View):
    def __init__(self, embed: hikari.Embed, maps: list, user1: hikari.User, user2: hikari.User) -> None:
        super().__init__(timeout=None, autodefer=True)
        self.turns = ['Ban', 'Ban', 'Pick', 'Pick', 'Ban', 'Ban']
        self.embed = embed
        self.maps = maps
        self.user1 = user1
        self.user2 = user2
        self.mapPicks = []
        self.sidePicks = []
        self.round = 1

    async def _handle_callback(self, item: ViewItem, ctx: ViewContext) -> None:
        select = ctx.interaction.values[0]
        
        try:
            self.maps.remove(select.capitalize())
        except ValueError:
            pass

        if len(self.maps) > 1:
            options = list()
            self.remove_item(item)
        
            options = [MapOption(map) for map in self.maps]
            self.add_item(MapSelection(options))

            if self.turns[self.round-1] in ['Pick']:
                self.mapPicks.append(select.capitalize())

            self.round += 1
            self.update_strike_text(select)
            await ctx.edit_response(self.embed, components=self.build())
        else:
            self.remove_item(item)
            self.add_item(SideSelection())

            if select not in ['ct', 't']:
                self.round = 1
                self.mapPicks.append(self.maps[0])
                map = self.mapPicks[self.round-1]
                embed = hikari.Embed(title=f'**{self.user2.global_name if self.round % 2 == 0 else self.user1.global_name}** choose your starting side on {map}:', color=get_setting('embed_color'))
                embed.set_image(f'assets/img/rushsite/maps/{map.lower()}.png')
                return await ctx.edit_response(embed, components=self.build())
            elif select == 't':
                self.sidePicks.append('Terrorist')
            else:
                self.sidePicks.append('Counter-Terrorist')

            if self.round == 3:
                embed = hikari.Embed(title=f'Strike Results:', description=f'\n`Map 1`: **{self.mapPicks[0]}**\n{self.user1.global_name} will start on **{self.sidePicks[0]}**\n{self.user2.global_name} will start on **{"Terrorist" if self.sidePicks[0] == "Counter-Terrorist" else "Counter-Terrorist"}**\n\n`Map 2`: **{self.mapPicks[1]}**\n{self.user2.global_name} will start on **{self.sidePicks[1]}**\n{self.user1.global_name} will start on **{"Terrorist" if self.sidePicks[1] == "Counter-Terrorist" else "Counter-Terrorist"}**\n\n`Map 3`: **{self.mapPicks[2]}**\n{self.user2.global_name} will start on **{self.sidePicks[2]}**\n{self.user1.global_name} will start on **{"Terrorist" if self.sidePicks[2] == "Counter-Terrorist" else "Counter-Terrorist"}**', color=get_setting('embed_color'))
                embed.set_image(f'assets/img/rushsite/maps/{self.mapPicks[0].lower()}.png')
                self.stop()
                return await ctx.edit_response(embed, components=[])

            self.round += 1
            self.turns = ['Pick']
            map = self.mapPicks[self.round-1]
            embed = hikari.Embed(title=f'**{self.user2.global_name}** choose your starting side on {map}:', color=get_setting('embed_color'))
            embed.set_image(f'assets/img/rushsite/maps/{map.lower()}.png')
            await ctx.edit_response(embed, components=self.build())

    async def view_check(self, ctx: ViewContext) -> bool:
        if self.round % 2 == 0 or self.turns[0] == 'Pick': # checks if round number is even
            return ctx.user.id == self.user2.id
        else:
            return ctx.user.id == self.user1.id
    
    def update_strike_text(self, map: str) -> None:
        if self.turns[self.round - 1] == 'Ban':
            try:
                self.embed.title = f'Turn {self.round}: {self.user2.global_name if self.round % 2 == 0 else self.user1.global_name} choose a stage to eliminate!'
                self.embed.description = f'**{map.capitalize()}** was elminated!' if self.turns[self.round - 2] == 'Ban' else f'**{map.capitalize()}** was chosen!'
            except IndexError:
                self.embed.title = f'Turn {self.round}: {self.user2.global_name if self.round % 2 == 0 else self.user1.global_name} choose a stage to eliminate!'
                self.embed.description = f'**{map.capitalize()}** was elminated!'
        else:
            try:
                self.embed.title = f'Turn {self.round}: {self.user2.global_name if self.round % 2 == 0 else self.user1.global_name} choose a stage for Map {len(self.mapPicks) + 1}!'
                self.embed.description = f'**{map.capitalize()}** was chosen!' if self.turns[self.round - 2] == 'Pick' else f'**{map.capitalize()}** was elminated!'
            except IndexError:
                self.embed.title = f'Turn {self.round}: {self.user2.global_name if self.round % 2 == 0 else self.user1.global_name} choose a stage for Map {len(self.mapPicks) + 1}!'
                self.embed.description = f'**{map.capitalize()}** was chosen!'
        return

@rushsite.child
@lightbulb.option('mode', 'Changes how striking works.', type=str, choices=['Pools','Playoffs'], required=True)
@lightbulb.option('user2', 'The user that will strike second.', type=hikari.User, required=True)
@lightbulb.option('user1', 'The user that will strike first.', type=hikari.User, required=True)
@lightbulb.option('maps', 'Provide a list by entering them separated with commas.', type=str, required=True)
@lightbulb.command('strike', 'Choose a map by taking turns elimitated maps one by one.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def strike(ctx: lightbulb.Context, maps: str, user1: hikari.User, user2: hikari.User, mode: str) -> None:
    if user1.is_bot or user2.is_bot:
        embed = hikari.Embed(description='You are not allowed to initiate a strike with a bot!', color=get_setting('embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif user1 == user2:
        embed = hikari.Embed(description='You are not allowed to initiate a strike with yourself!', color=get_setting('embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    mapList = maps.replace(' ', '').split(',')
    options = list()
    embed = hikari.Embed(title=f'Turn 1: {user1.global_name} choose a stage to eliminate!', color=get_setting('embed_color'))
    embed.set_image('assets/img/rushsite/maps/stage_list.png')
    
    for map in mapList:
        options.append(MapOption(map))
    
    if mode == 'Pools':
        view = StrikeViewPools(embed, mapList, user1, user2)
    else:
        if len(mapList) != 7:
            embed = hikari.Embed(description='Map list has to include 7 maps!', color=get_setting('embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        view = StrikeViewPlayoffs(embed, mapList, user1, user2)
    
    view.add_item(MapSelection(options))
    message = await ctx.respond(embed, components=view.build())
    
    await view.start(message)


## SignUp Command ##

@rushsite.child
@lightbulb.command('register', 'Register now for the latest Rushsite tournament!', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def signup(ctx: lightbulb.Context) -> None:
    embed = hikari.Embed(title='Rushsite Tournament Registration', description=f"Join us and sign up for the latest [Rushsite tournament]({get_setting('rushsite_register_link')})!\nDon't miss the action, as the tournament will be streamed live on [Twitch](https://twitch.tv/ryqb)!", color=get_setting('embed_color'))
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

## Search Command ##

@rushsite.child
@lightbulb.option('name', 'The name of the player or team.', type=str, autocomplete=True, required=True)
@lightbulb.command('search', 'Get info about this player or team.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def search(ctx: lightbulb.Context, name: str) -> None:
    if name not in allNames[0] + allNames[1]: # If name is not in teams or players
        embed = (hikari.Embed(description=f'The player or team name cannot be found.', color=get_setting('embed_error_color')))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif name in allNames[0]: # If name is a team
        teamName = allNames[0][allNames[0].index(name)]
        
        try:
            wins, draws, losses, mapsPlayed, avgGroupPoints, avgGroupPlacing, avgFinalPlacing, trophies, tWinRate, ctWinRate, commonSide, commonMap = rushsiteStats['Teams'][teamName].values()
        except ValueError:
            wins, draws, losses, mapsPlayed, avgGroupPoints, avgGroupPlacing, avgFinalPlacing, trophies, commonSide, commonMap = rushsiteStats['Teams'][teamName].values()
            tWinRate = None
            ctWinRate = None
        if commonSide == ['Even']:
            commonSide = ['CT', 'T']
        
        thumbnail = f'assets/img/rushsite/logos/{str(teamName).lower().replace(" ", "")}.png'
        embed = (hikari.Embed(title=f'Team: {teamName} {" ".join([f"{chr(92)}🏆" for i in range(int(trophies))])}', color=get_setting('embed_color'), timestamp=datetime.now().astimezone()))
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
        wins, draws, losses, kills, assists, deaths, mvp, score, ud, ef, rp, dmg, hsk, trophies, teams = rushsiteStats['Players'][playerName].values()
        thumbnail = f'assets/img/rushsite/logos/{str(teams[len(teams)-1]).lower().replace(" ", "")}.png'
        
        try:
            kdr = kills/deaths
        except ZeroDivisionError:
            kdr = 0
        
        embed = (hikari.Embed(title=f'Player: {playerName} ({", ".join(teams)}) {" ".join([f"{chr(92)}🏆" for i in range(int(trophies))])}', color=get_setting('embed_color'), timestamp=datetime.now().astimezone()))
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

## Top Command ##

@rushsite.child
@lightbulb.option('stat', 'The name of the stat.', type=str, choices=['Wins','Draws','Losses','Kills','Assists','Deaths','MVPs','Score','Damage','Utility Damage','Enemies Flashed','Rounds Played','Headshot Kills','Tournament Victories'], required=True)
@lightbulb.command('top', 'Get the top 10 players based on chosen stat.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def search(ctx: lightbulb.Context, stat: str) -> None:
    statDict = {'Wins': 'Wins', 'Draws': 'Draws', 'Losses': 'Losses', 'Kills': 'K', 'Assists': 'A', 'Deaths': 'D', 'MVPs': 'MVP', 'Score': 'SCORE', 'Utility Damage': 'UD', 'Enemies Flashed': 'EF', 'Rounds Played': 'RP', 'Damage': 'DMG', 'Headshot Kills': 'HSK', 'Tournament Victories': 'Trophies'}
    amount = 10
    
    users, values = get_top_stats(rushsiteStats['Players'], statDict.get(stat), amount)

    embed = hikari.Embed(title=f'Top {amount} players based on {stat}', color=get_setting('embed_color'), timestamp=datetime.now().astimezone())
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

## Error Handler ##

@plugin.set_error_handler()
async def on_command_error(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event.exception, lightbulb.CommandNotFound):
        return
    if isinstance(event.exception, lightbulb.NotEnoughArguments):
        embed = (hikari.Embed(description='Not enough arguments were passed.\n' + ', '.join(event.exception.args), color=get_setting('embed_error_color')))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    if isinstance(event.exception, lightbulb.CommandIsOnCooldown):
        embed = (hikari.Embed(description=f'Command is on cooldown. Try again in {round(event.exception.retry_after)} second(s).', color=get_setting('embed_error_color')))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    if isinstance(event.exception, lightbulb.NotOwner):
        embed = (hikari.Embed(description=f'You do not have permission to use this command!', color=get_setting('embed_error_color')))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    embed = (hikari.Embed(description='I have errored, and I cannot get up', color=get_setting('embed_error_color')))
    await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    raise event.exception

## Definitions ##

def load(bot):
    bot.add_plugin(plugin)