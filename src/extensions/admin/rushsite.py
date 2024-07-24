import os
import hikari
import lightbulb
import miru
import random

from miru.abc.item import ViewItem
from miru.context import ViewContext

from miru.context.view import ViewContext
from bot import get_setting

plugin = lightbulb.Plugin('Rushsite Admin')

@plugin.command
@lightbulb.app_command_permissions(perms=hikari.Permissions.MANAGE_CHANNELS, dm_enabled=False)
@lightbulb.command('rushsite-admin', 'Access administrative privileges for Rushsite commands.')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def rushsite_admin(ctx: lightbulb.Context) -> None:
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
        super().__init__(options=[miru.SelectOption(label='Counter-Terrorist', emoji='<:CounterTerrorist:1265770646739353684>', value='ct'), miru.SelectOption(label='Terrorist', emoji='<:Terrorist:1139272220884091001>', value='t')], custom_id='side_select', placeholder='Pick a Side')

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
                embed = hikari.Embed(title=f'**{self.user2.global_name}** choose your starting side on {winner}:', color=get_setting('general', 'embed_color'))
                embed.set_image(f'assets/img/rushsite/maps/{winner.lower()}.png')
                await ctx.edit_response(embed, components=self.build())
            elif select == 't':
                embed = hikari.Embed(title=f'Strike Results:', description=f'The chosen map is **{winner}**!\n\n{self.user2.global_name} will start on **Terrorist**\n{self.user1.global_name} will start on **Counter-Terrorist**', color=get_setting('general', 'embed_color'))
                embed.set_image(f'assets/img/rushsite/maps/{winner.lower()}.png')
                await ctx.edit_response(embed, components=[])
                self.stop()
            else:
                embed = hikari.Embed(title=f'Strike Results:', description=f'The chosen map is **{winner}**!\n\n{self.user2.global_name} will start on **Counter-Terrorist**\n{self.user1.global_name} will start on **Terrorist**', color=get_setting('general', 'embed_color'))
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
        self.embed.description = f'**{map.capitalize()}** was eliminated!'
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
                embed = hikari.Embed(title=f'**{self.user2.global_name if self.round % 2 == 0 else self.user1.global_name}** choose your starting side on {map}:', color=get_setting('general', 'embed_color'))
                embed.set_image(f'assets/img/rushsite/maps/{map.lower()}.png')
                return await ctx.edit_response(embed, components=self.build())
            elif select == 't':
                self.sidePicks.append('Terrorist')
            else:
                self.sidePicks.append('Counter-Terrorist')

            if self.round == 3:
                embed = hikari.Embed(title=f'Strike Results:', description=f'\n`Map 1`: **{self.mapPicks[0]}**\n{self.user1.global_name} will start on **{self.sidePicks[0]}**\n{self.user2.global_name} will start on **{"Terrorist" if self.sidePicks[0] == "Counter-Terrorist" else "Counter-Terrorist"}**\n\n`Map 2`: **{self.mapPicks[1]}**\n{self.user2.global_name} will start on **{self.sidePicks[1]}**\n{self.user1.global_name} will start on **{"Terrorist" if self.sidePicks[1] == "Counter-Terrorist" else "Counter-Terrorist"}**\n\n`Map 3`: **{self.mapPicks[2]}**\n{self.user2.global_name} will start on **{self.sidePicks[2]}**\n{self.user1.global_name} will start on **{"Terrorist" if self.sidePicks[2] == "Counter-Terrorist" else "Counter-Terrorist"}**', color=get_setting('general', 'embed_color'))
                embed.set_image(f'assets/img/rushsite/maps/{self.mapPicks[0].lower()}.png')
                self.stop()
                return await ctx.edit_response(embed, components=[])

            self.round += 1
            self.turns = ['Pick']
            map = self.mapPicks[self.round-1]
            embed = hikari.Embed(title=f'**{self.user2.global_name}** choose your starting side on {map}:', color=get_setting('general', 'embed_color'))
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
                self.embed.description = f'**{map.capitalize()}** was eliminated!' if self.turns[self.round - 2] == 'Ban' else f'**{map.capitalize()}** was chosen!'
            except IndexError:
                self.embed.title = f'Turn {self.round}: {self.user2.global_name if self.round % 2 == 0 else self.user1.global_name} choose a stage to eliminate!'
                self.embed.description = f'**{map.capitalize()}** was eliminated!'
        else:
            try:
                self.embed.title = f'Turn {self.round}: {self.user2.global_name if self.round % 2 == 0 else self.user1.global_name} choose a stage for Map {len(self.mapPicks) + 1}!'
                self.embed.description = f'**{map.capitalize()}** was chosen!' if self.turns[self.round - 2] == 'Pick' else f'**{map.capitalize()}** was eliminated!'
            except IndexError:
                self.embed.title = f'Turn {self.round}: {self.user2.global_name if self.round % 2 == 0 else self.user1.global_name} choose a stage for Map {len(self.mapPicks) + 1}!'
                self.embed.description = f'**{map.capitalize()}** was chosen!'
        return

@rushsite_admin.child
@lightbulb.option('mode', 'Changes how striking works.', type=str, choices=['Pools','Playoffs'], required=True)
@lightbulb.option('user2', 'The user that will strike second.', type=hikari.User, required=True)
@lightbulb.option('user1', 'The user that will strike first.', type=hikari.User, required=True)
@lightbulb.option('maps', 'Provide a list by entering them separated with commas.', type=str, required=True)
@lightbulb.command('strike', 'Choose a map by taking turns eliminated maps one by one.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def strike(ctx: lightbulb.Context, maps: str, user1: hikari.User, user2: hikari.User, mode: str) -> None:
    if user1.is_bot or user2.is_bot:
        embed = hikari.Embed(description='You are not allowed to initiate a strike with a bot!', color=get_setting('general', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    elif user1 == user2:
        embed = hikari.Embed(description='You are not allowed to initiate a strike with yourself!', color=get_setting('general', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    mapList = maps.replace(' ', '').split(',')
    options = list()
    embed = hikari.Embed(title=f'Turn 1: {user1.global_name} choose a stage to eliminate!', color=get_setting('general', 'embed_color'))
    embed.set_image('assets/img/rushsite/maps/stage_list.png')
    
    for map in mapList:
        options.append(MapOption(map))
    
    if mode == 'Pools':
        view = StrikeViewPools(embed, mapList, user1, user2)
    else:
        if len(mapList) != 7:
            embed = hikari.Embed(description='Map list has to include 7 maps!', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        view = StrikeViewPlayoffs(embed, mapList, user1, user2)
    
    view.add_item(MapSelection(options))
    message = await ctx.respond(embed, components=view.build())
    
    await view.start(message)

## Generate Pools ##

@rushsite_admin.child
@lightbulb.option('groups', 'Number of groups to evenly distributing them into.', type=int, required=True)
@lightbulb.option('teams', 'Provide a list of teams by entering them separated with commas.', type=str, required=True)
@lightbulb.command('pools', 'Generates randomized pools of teams from a given list.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def pools(ctx: lightbulb.Context, teams: str, groups: int) -> None:
    teamList = teams.replace(' ', '').split(',')

    if len(teamList) < groups:
        embed = (hikari.Embed(description=f'Group number is larger than the team list!', color=get_setting('general', 'embed_error_color')))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    
    embed = hikari.Embed(title=f'Generated Pools', color=get_setting('general', 'embed_color'))
    teamsPerGroup, remainder = divmod(len(teamList), groups)
    teamIter = iter(teamList)
    groupList = [[] for _ in range(groups)]

    random.shuffle(teamList)
    for group in groupList:
        for _ in range(teamsPerGroup):
            try:
                team = next(teamIter)
                group.append(team)
            except StopIteration:
                break
    
    for i, team in enumerate(teamIter):
        groupList[i % groups].append(team)
    
    for i, group in enumerate(groupList, start=1):
        embed.add_field(name=f'Group {i}', value=f'> {f"{chr(10)}> ".join(group)}', inline=True)
    
    await ctx.respond(embed)
    
def load(bot):
    bot.add_plugin(plugin)