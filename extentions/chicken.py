import hikari
import lightbulb
import miru
import sqlite3
import random
import asyncio

from datetime import datetime
from bot import get_setting, verify_user
from .economy import remove_money

plugin = lightbulb.Plugin('Chicken')

wild = []
prepareTimer = 15.0
combatTimer = 1.0

## Cock Subcommand ##

@plugin.command
@lightbulb.command('cock', 'Every command related to chickens.')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommandGroup)
async def cock(ctx: lightbulb.Context) -> None:
    return

## Info Command ##

@cock.child
@lightbulb.option('user', 'The user to get information about.', type=hikari.User, required=False)
@lightbulb.command('info', "Shows info about a sever member's cock (CHICKEN!).", aliases=['cock'], pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def cock_info(ctx: lightbulb.Context, user: hikari.User) -> None:
    if user == None: # if no user has been sent
        user = ctx.author
    elif user.is_bot: # user has been sent. checks if user is a bot
        embed = hikari.Embed(description="Bots don't have the rights to raise cocks!", color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    if verify_user(user) == None: # if user has never been register
        embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    userCock = get_cock_info(user)
    userCock = add_item_to_stats(userCock)
    
    items = items_to_list(userCock.get('items'))
    strItems = []
    for i in items:
        strItems.append(f'`{i}`')
    strItems = ', \n'.join(strItems)
    
    embed = (hikari.Embed(title=f"{user.username}'s {userCock.get('name')} (lvl {userCock.get('level')})", description=f"They have been companions since `{userCock.get('date')}`.", color=get_setting('embed_color')))
    embed.set_thumbnail(fr'''chickens\{userCock.get('name').lower()}.png''')
    embed.add_field(name=f"{userCock.get('name')}'s Stats", value=f"Experience: `{userCock.get('experience')}/100` \nHealth: {userCock.get('health')} ❤️\nStrength: {userCock.get('strength')} 👊\nDefense: {userCock.get('defense')} 🛡️\nHit Rate: {userCock.get('hit')} 🎯", inline=True)
    embed.add_field(name='Held Items', value=strItems, inline=True)
    
    await ctx.respond(embed)

## Shop Command ##

@cock.child
@lightbulb.command('shop', 'Start your chicken raising adventure!', aliases=['shop'])
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def cock_shop(ctx: lightbulb.Context) -> None:
    embed = hikari.Embed(title='Welcome to the Cock Shop!', description='Start your cock fighting adventure by purchasing your very own cock! \nKeep in mind that you can only raise 1 cock at a time!', color=get_setting('embed_color'))
    embed.add_field(name='Baby Chick (lvl 1)', value='Health: 10 ❤️\nAttack: 1 👊\nDefense: 0 🛡️\n**Cost: 🪙 300**', inline=True)
    embed.add_field(name='Cockerel (lvl 1)', value='Health: 20 ❤️\nAttack: 2 👊\nDefense: 1 🛡️\n**Cost: 🪙 1000**', inline=True)
    embed.add_field(name='Rooster (lvl 1)', value='Health: 40 ❤️\nAttack: 4 👊\nDefense: 2 🛡️\n**Cost: 🪙 2000**', inline=True)
    
    view = ShopView(ctx.author)
    
    message = await ctx.respond(embed, components=view.build())
    message = await message
    
    await view.start(message)

class ShopView(miru.View):
    def __init__(self, author: hikari.User) -> None:
        super().__init__(timeout=None)
        self.author = author
    
    @miru.button(label='Baby Chick', emoji='🐣', style=hikari.ButtonStyle.PRIMARY, row=1)
    async def baby(self, button: miru.Button, ctx: miru.Context) -> None:
        cockInfo ={'amount': 300, 'name': 'Chick', 'level': 1, 'experience': 0, 'health': 10, 'strength': 1, 'defense': 0, 'hit': 70, 'items': 'None'}
        user = ctx.user
        
        if verify_user(user) == None: # if user has never been register
            embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif has_cock(user):
            embed = hikari.Embed(description='You already own a cock!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif remove_money(user.id, cockInfo.get('amount'), True) == False: # checks if user has enough money
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        try:
            add_cock(user, cockInfo.get('name'), datetime.now().strftime(r"%m/%d/%Y"), cockInfo.get('level'), cockInfo.get('experience'), cockInfo.get('health'), cockInfo.get('strength'), cockInfo.get('defense'), cockInfo.get('hit'), cockInfo.get('items'))
            embed = (hikari.Embed(title='Success!', description=f"{user.username} purchased a Baby Chick for 🪙 {cockInfo.get('amount')}!", color=get_setting('embed_success_color')))
        except:
            embed = hikari.Embed(description="Failed to purchase cock!", color=get_setting('embed_error_color'))
        
        await ctx.respond(embed)
    
    @miru.button(label='Cockerel', emoji='🐥', style=hikari.ButtonStyle.PRIMARY, row=1)
    async def child(self, button: miru.Button, ctx: miru.Context) -> None:        
        cockInfo ={'amount': 1000, 'name': 'Cockerel', 'level': 1, 'experience': 0, 'health': 20, 'strength': 2, 'defense': 1, 'hit': 70, 'items': 'None'}
        user = ctx.user
        
        if verify_user(user) == None: # if user has never been register
            embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif has_cock(user):
            embed = hikari.Embed(description='You already own a cock!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif remove_money(user.id, cockInfo.get('amount'), True) == False: # checks if user has enough money
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        try:
            add_cock(user, cockInfo.get('name'), datetime.now().strftime(r"%m/%d/%Y"), cockInfo.get('level'), cockInfo.get('experience'), cockInfo.get('health'), cockInfo.get('strength'), cockInfo.get('defense'), cockInfo.get('hit'), cockInfo.get('items'))
            embed = (hikari.Embed(title='Success!', description=f"{user.username} purchased a Baby Chick for 🪙 {cockInfo.get('amount')}!", color=get_setting('embed_success_color')))
        except:
            embed = hikari.Embed(description="Failed to purchase cock!", color=get_setting('embed_error_color'))
        
        await ctx.respond(embed)
    
    @miru.button(label='Rooster', emoji='🐔', style=hikari.ButtonStyle.PRIMARY, row=1)
    async def adult(self, button: miru.Button, ctx: miru.Context) -> None:
        cockInfo ={'amount': 2000, 'name': 'Rooster', 'level': 1, 'experience': 0, 'health': 40, 'strength': 4, 'defense': 2, 'hit': 70, 'items': 'None'}
        user = ctx.user
        
        if verify_user(user) == None: # if user has never been register
            embed = hikari.Embed(description="You don't have a balance! Type in chat at least once!", color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif has_cock(user):
            embed = hikari.Embed(description='You already own a cock!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif remove_money(user.id, cockInfo.get('amount'), True) == False: # checks if user has enough money
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        try:
            add_cock(user, cockInfo.get('name'), datetime.now().strftime(r"%m/%d/%Y"), cockInfo.get('level'), cockInfo.get('experience'), cockInfo.get('health'), cockInfo.get('strength'), cockInfo.get('defense'), cockInfo.get('hit'), cockInfo.get('items'))
            embed = (hikari.Embed(title='Success!', description=f"{user.username} purchased a Baby Chick for 🪙 {cockInfo.get('amount')}!", color=get_setting('embed_success_color')))
        except:
            embed = hikari.Embed(description="Failed to purchase cock!", color=get_setting('embed_error_color'))
        
        await ctx.respond(embed)
    
    async def view_check(self, ctx: miru.Context) -> bool:
        return ctx.user.id == self.author.id

## Wilderness Command ##

@cock.child
@lightbulb.command('wilderness', 'Enter the wilderness to fight wild cocks to gain experience and items!')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def wilderness(ctx: lightbulb.Context) -> None:
    if has_cock(ctx.user) == False:
        embed = hikari.Embed(title='This user does not own a cock!', description='Type `/cock-shop` to purchase one!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif player_in_wild(ctx.user.id):
        embed = hikari.Embed(description='Your cock is currently in the wilderness!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    embed = hikari.Embed(title='You entered the wilderness!', description="While in the wilderness, you can choose a selection of wild cocks! However, initiating a battle against undomesticated cocks will cost a certain amount of coins (🪙 50, 🪙 100, 🪙 150). Tougher cocks have a higher chance of dropping more experience and held items! \n\nLosing in a fight will result in losing all experience points, be careful! \n\n`Note: Your level will remain the same if you white out.`", color=get_setting('embed_color'))
    embed.set_image(r'''chickens\wilderness.png''')
    
    view = WildernessView()
    
    message = await ctx.respond(embed, components=view.build())
    message = await message
    
    wild.append(ctx.author.id)  
    
    await view.start(message)
    await view.wait()
    
    wild.remove(ctx.author.id) 

class WildernessView(miru.View):
    def __init__(self) -> None:
        super().__init__(timeout=120.0)   
        
    @miru.button(label='Wild Chick', emoji='🐣', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def easy(self, button: miru.Button, ctx: miru.Context) -> None:
        if remove_money(ctx.user.id, 50, True) == False:
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        # super().__init__(timeout=None)
        userCock = get_cock_info(ctx.user) # grabs user's stats
        wildCock = generate_wild_cock('Chick', userCock.get('level'), userCock.get('health'), userCock.get('strength'), userCock.get('defense'))
        
        userCock = add_item_to_stats(userCock)
        
        embed = (hikari.Embed(title='You encountered a wild chick!', description='`The auto battle will commence shortly...`', color=get_setting('embed_color')))
        embed.set_image(None)
        embed.set_thumbnail(r'''chickens\chick.png''')
        embed.add_field(name=f"{ctx.user.username}'s {userCock.get('name')} (lvl {userCock.get('level')})", value=f"Health: {userCock.get('health')} ❤️\nStrength: {userCock.get('strength')} 👊\nDefense: {userCock.get('defense')} 🛡️\nHit Rate: {userCock.get('hit')} 🎯", inline=True)
        embed.add_field(name=f"Wild Chick (lvl {wildCock.get('level')})", value=f"Health: {wildCock.get('health')} ❤️\nStrength: {wildCock.get('strength')} 👊\nDefense: {wildCock.get('defense')} 🛡️\nHit Rate: {wildCock.get('hit')} 🎯", inline=True)
    
        await ctx.edit_response(embed, components=[])
        
        await asyncio.sleep(prepareTimer) # waiting for the fight to start
        
        turn = 1
        
        while userCock.get('health') > 0 and wildCock.get('health') > 0:
            if player_turn(turn):
                if random.randint(1, 100) <= userCock.get('hit'):
                    wildCock['health'] = wildCock['health'] - get_cock_damage(turn, userCock, wildCock)
                    embed = (hikari.Embed(title='You encountered a wild chick!', description=f"__**Turn {turn}**__ \n`{ctx.user.username}'s {userCock.get('name')} dealt {get_cock_damage(turn, userCock, wildCock)}❤️`", color=get_setting('embed_color')))
                else:
                    embed = (hikari.Embed(title='You encountered a wild chick!', description=f"__**Turn {turn}**__ \n`{ctx.user.username}'s {userCock.get('name')} missed!`", color=get_setting('embed_color')))
            else:
                if random.randint(1, 100) <= wildCock.get('hit'):
                    userCock['health'] = userCock['health'] - get_cock_damage(turn, userCock, wildCock)
                    embed = (hikari.Embed(title='You encountered a wild chick!', description=f"__**Turn {turn}**__ \n`Wild Chick dealt {get_cock_damage(turn, userCock, wildCock)}❤️`", color=get_setting('embed_color')))
                else:
                    embed = (hikari.Embed(title='You encountered a wild chick!', description=f"__**Turn {turn}**__ \n`Wild Chick missed!`", color=get_setting('embed_color')))
            
            embed.set_thumbnail(r'''chickens\chick.png''') 
            embed.add_field(name=f"{ctx.user.username}'s {userCock.get('name')} (lvl {userCock.get('level')})", value=f"Health: {userCock.get('health')} ❤️\nStrength: {userCock.get('strength')} 👊\nDefense: {userCock.get('defense')} 🛡️\nHit Rate: {userCock.get('hit')} 🎯", inline=True)
            embed.add_field(name=f"Wild Chick (lvl {wildCock.get('level')})", value=f"Health: {wildCock.get('health')} ❤️\nStrength: {wildCock.get('strength')} 👊\nDefense: {wildCock.get('defense')} 🛡️\nHit Rate: {wildCock.get('hit')} 🎯", inline=True)
            await ctx.edit_response(embed)
            
            turn = turn + 1
            
            await asyncio.sleep(combatTimer) # turn delay
        
        if userCock.get('health') > 0:
            experience = random.randint(4, 12)
            newCock = add_exp(ctx.user, experience)
            embed.add_field(name='You won!', value=f'`You gained {experience}🧪`')
            if newCock.get('level_up'):
                embed.add_field(name=f"Your {userCock.get('name')} leveled up to lvl {newCock.get('level')}!", value=f"`{newCock.get('old_health')}❤️` → `{newCock.get('new_health')}❤️` \n`{newCock.get('old_strength')}👊` → `{newCock.get('new_strength')}👊` \n`{newCock.get('old_defense')}🛡️` → `{newCock.get('new_defense')}🛡️`")
            if random.randint(1, 240) == 1:
                item = item_loot_drop(ctx.user)
                embed.add_field(name='You found an item!', value=f'`{item}`')
            
            wild.remove(ctx.author.id)
            await ctx.edit_response(embed)
            
            return
        
        reset_exp(ctx.user)
        embed.add_field(name='You whited out!', value=f"`You fled unharmed at the cost of losing all your cock's experience points!`")
        wild.remove(ctx.author.id)
        await ctx.edit_response(embed)
    
    @miru.button(label='Wild Cockerel', emoji='🐥', style=hikari.ButtonStyle.PRIMARY, row=1)
    async def normal(self, button: miru.Button, ctx: miru.Context) -> None:
        if remove_money(ctx.user.id, 100, True) == False:
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        # super().__init__(timeout=None)
        userCock = get_cock_info(ctx.user)
        wildCock = generate_wild_cock('Cockerel', userCock.get('level'), userCock.get('health'), userCock.get('strength'), userCock.get('defense'))
        
        userCock = add_item_to_stats(userCock)
        
        embed = (hikari.Embed(title='You encountered a wild cockerel!', description='`The auto battle will commence shortly...`', color=get_setting('embed_color')))
        embed.set_image(None)
        embed.set_thumbnail(r'''chickens\cockerel.png''')
        embed.add_field(name=f"{ctx.user.username}'s {userCock.get('name')} (lvl {userCock.get('level')})", value=f"Health: {userCock.get('health')} ❤️\nStrength: {userCock.get('strength')} 👊\nDefense: {userCock.get('defense')} 🛡️\nHit Rate: {userCock.get('hit')} 🎯", inline=True)
        embed.add_field(name=f"Wild Cockerel (lvl {wildCock.get('level')})", value=f"Health: {wildCock.get('health')} ❤️\nStrength: {wildCock.get('strength')} 👊\nDefense: {wildCock.get('defense')} 🛡️\nHit Rate: {wildCock.get('hit')} 🎯", inline=True)
    
        await ctx.edit_response(embed, components=[])
        
        await asyncio.sleep(prepareTimer) # waiting for the fight to start
        
        turn = 1
        
        while userCock.get('health') > 0 and wildCock.get('health') > 0:
            if player_turn(turn):
                if random.randint(1, 100) <= userCock.get('hit'):
                    wildCock['health'] = wildCock['health'] - get_cock_damage(turn, userCock, wildCock)
                    embed = (hikari.Embed(title='You encountered a wild cockerel!', description=f"__**Turn {turn}**__ \n`{ctx.user.username}'s {userCock.get('name')} dealt {get_cock_damage(turn, userCock, wildCock)}❤️`", color=get_setting('embed_color')))
                else:
                    embed = (hikari.Embed(title='You encountered a wild cockerel!', description=f"__**Turn {turn}**__ \n`{ctx.user.username}'s {userCock.get('name')} missed!`", color=get_setting('embed_color')))
            else:
                if random.randint(1, 100) <= wildCock.get('hit'):
                    userCock['health'] = userCock['health'] - get_cock_damage(turn, userCock, wildCock)
                    embed = (hikari.Embed(title='You encountered a wild cockerel!', description=f"__**Turn {turn}**__ \n`Wild Cockerel dealt {get_cock_damage(turn, userCock, wildCock)}❤️`", color=get_setting('embed_color')))
                else:
                    embed = (hikari.Embed(title='You encountered a wild cockerel!', description=f"__**Turn {turn}**__ \n`Wild Cockerel missed!`", color=get_setting('embed_color')))
            
            embed.set_thumbnail(r'''chickens\cockerel.png''') 
            embed.add_field(name=f"{ctx.user.username}'s {userCock.get('name')} (lvl {userCock.get('level')})", value=f"Health: {userCock.get('health')} ❤️\nStrength: {userCock.get('strength')} 👊\nDefense: {userCock.get('defense')} 🛡️\nHit Rate: {userCock.get('hit')} 🎯", inline=True)
            embed.add_field(name=f"Wild Cockerel (lvl {wildCock.get('level')})", value=f"Health: {wildCock.get('health')} ❤️\nStrength: {wildCock.get('strength')} 👊\nDefense: {wildCock.get('defense')} 🛡️\nHit Rate: {wildCock.get('hit')} 🎯", inline=True)
            await ctx.edit_response(embed)
            
            turn = turn + 1
            
            await asyncio.sleep(combatTimer) # turn delay
        
        if userCock.get('health') > 0:
            experience = random.randint(12, 23)
            newCock = add_exp(ctx.user, experience)
            embed.add_field(name='You won!', value=f'`You gained {experience}🧪`')
            if newCock.get('level_up'):
                embed.add_field(name=f"Your {userCock.get('name')} leveled up to lvl {newCock.get('level')}!", value=f"`{newCock.get('old_health')}❤️` → `{newCock.get('new_health')}❤️` \n`{newCock.get('old_strength')}👊` → `{newCock.get('new_strength')}👊` \n`{newCock.get('old_defense')}🛡️` → `{newCock.get('new_defense')}🛡️`")
            if random.randint(1, 60) == 1:
                item = item_loot_drop(ctx.user)
                embed.add_field(name='You found an item!', value=f'`{item}`')
            
            wild.remove(ctx.author.id)
            await ctx.edit_response(embed)
            
            return
        
        reset_exp(ctx.user)
        embed.add_field(name='You whited out!', value=f"`You fled unharmed at the cost of losing all your cock's experience points!`")
        wild.remove(ctx.author.id)
        await ctx.edit_response(embed)
    
    @miru.button(label='Wild Rooster', emoji='🐔', style=hikari.ButtonStyle.DANGER, row=1)
    async def hard(self, button: miru.Button, ctx: miru.Context) -> None:
        if remove_money(ctx.user.id, 150, True) == False:
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        # super().__init__(timeout=None)
        userCock = get_cock_info(ctx.user)
        wildCock = generate_wild_cock('Rooster', userCock.get('level'), userCock.get('health'), userCock.get('strength'), userCock.get('defense'))
        
        userCock = add_item_to_stats(userCock)
        
        embed = (hikari.Embed(title='You encountered a wild rooster!', description='`The auto battle will commence shortly...`', color=get_setting('embed_color')))
        embed.set_image(None)
        embed.set_thumbnail(r'''chickens\rooster.png''')
        embed.add_field(name=f"{ctx.user.username}'s {userCock.get('name')} (lvl {userCock.get('level')})", value=f"Health: {userCock.get('health')} ❤️\nStrength: {userCock.get('strength')} 👊\nDefense: {userCock.get('defense')} 🛡️\nHit Rate: {userCock.get('hit')} 🎯", inline=True)
        embed.add_field(name=f"Wild Rooster (lvl {wildCock.get('level')})", value=f"Health: {wildCock.get('health')} ❤️\nStrength: {wildCock.get('strength')} 👊\nDefense: {wildCock.get('defense')} 🛡️\nHit Rate: {wildCock.get('hit')} 🎯", inline=True)
    
        await ctx.edit_response(embed, components=[])
        
        await asyncio.sleep(prepareTimer) # waiting for the fight to start
        
        turn = 1
        
        while userCock.get('health') > 0 and wildCock.get('health') > 0:
            if player_turn(turn):
                if random.randint(1, 100) <= userCock.get('hit'):
                    wildCock['health'] = wildCock['health'] - get_cock_damage(turn, userCock, wildCock)
                    embed = (hikari.Embed(title='You encountered a wild rooster!', description=f"__**Turn {turn}**__ \n`{ctx.user.username}'s {userCock.get('name')} dealt {get_cock_damage(turn, userCock, wildCock)}❤️`", color=get_setting('embed_color')))
                else:
                    embed = (hikari.Embed(title='You encountered a wild rooster!', description=f"__**Turn {turn}**__ \n`{ctx.user.username}'s {userCock.get('name')} missed!`", color=get_setting('embed_color')))
            else:
                if random.randint(1, 100) <= wildCock.get('hit'):
                    userCock['health'] = userCock['health'] - get_cock_damage(turn, userCock, wildCock)
                    embed = (hikari.Embed(title='You encountered a wild rooster!', description=f"__**Turn {turn}**__ \n`Wild Rooster dealt {get_cock_damage(turn, userCock, wildCock)}❤️`", color=get_setting('embed_color')))
                else:
                    embed = (hikari.Embed(title='You encountered a wild rooster!', description=f"__**Turn {turn}**__ \n`Wild Rooster missed!`", color=get_setting('embed_color')))
            
            embed.set_thumbnail(r'''chickens\rooster.png''') 
            embed.add_field(name=f"{ctx.user.username}'s {userCock.get('name')} (lvl {userCock.get('level')})", value=f"Health: {userCock.get('health')} ❤️\nStrength: {userCock.get('strength')} 👊\nDefense: {userCock.get('defense')} 🛡️\nHit Rate: {userCock.get('hit')} 🎯", inline=True)
            embed.add_field(name=f"Wild Rooster (lvl {wildCock.get('level')})", value=f"Health: {wildCock.get('health')} ❤️\nStrength: {wildCock.get('strength')} 👊\nDefense: {wildCock.get('defense')} 🛡️\nHit Rate: {wildCock.get('hit')} 🎯", inline=True)
            await ctx.edit_response(embed)
            
            turn = turn + 1
            
            await asyncio.sleep(combatTimer) # turn delay
        
        if userCock.get('health') > 0:
            experience = random.randint(24, 36)
            newCock = add_exp(ctx.user, experience)
            embed.add_field(name='You won!', value=f'`You gained {experience}🧪`')
            if newCock.get('level_up'):
                embed.add_field(name=f"Your {userCock.get('name')} leveled up to lvl {newCock.get('level')}!", value=f"`{newCock.get('old_health')}❤️` → `{newCock.get('new_health')}❤️` \n`{newCock.get('old_strength')}👊` → `{newCock.get('new_strength')}👊` \n`{newCock.get('old_defense')}🛡️` → `{newCock.get('new_defense')}🛡️`")
            if random.randint(1, 25) == 1:
                item = item_loot_drop(ctx.user)
                embed.add_field(name='You found an item!', value=f'`{item}`')
            
            wild.remove(ctx.author.id)
            await ctx.edit_response(embed)
            
            return
        
        reset_exp(ctx.user)
        embed.add_field(name='You whited out!', value=f"`You fled unharmed at the cost of losing all your cock's experience points!`")
        wild.remove(ctx.author.id)
        await ctx.edit_response(embed)
    
    async def on_timeout(self) -> None:
        try:
            embed = hikari.Embed(title='You left the wilderness!', description='You escaped from the wilderness unscathed.', color=get_setting('embed_color'))
            embed.set_image(r'''chickens\wilderness.png''')
            await self.message.edit(embed, components=[])
            
            self.stop()
        except:
            pass
    
    async def view_check(self, ctx: miru.Context) -> bool:
        return ctx.user.id == ctx.author.id

## Friendly Command ##

@cock.child
@lightbulb.option('user', 'The user to get information about.', type=hikari.User, required=False)
@lightbulb.command('friendly', 'Fight a friendly match with a server member!')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def friendly(ctx: lightbulb.Context) -> None:
    embed = hikari.Embed(description='This feature has not been implemented yet!', color=get_setting('embed_error_color'))
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

## Sell Command ##

@cock.child
@lightbulb.command('sell', 'Are you bored of your feathered friend? Sell them for some coins!')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def friendly(ctx: lightbulb.Context) -> None:
    embed = hikari.Embed(description='This feature has not been implemented yet!', color=get_setting('embed_error_color'))
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

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

def has_cock(user: hikari.User) -> bool:
    db = sqlite3.connect('database.sqlite')
    cursor = db.cursor()
    
    cursor.execute(f'SELECT breed FROM chicken WHERE user_id = {user.id}') # moves cursor to user's chicken info from database
    val = cursor.fetchone() # grabs the values of user's chicken
    
    try:
        chicken = val[0]
    except:
        chicken = 'N/A'
    
    if chicken == 'N/A':
        return False
    
    return True

def add_cock(user: hikari.User, name: str, date: str, level: int, exp: int, health: int, strength: int, defense: int, hit: int, items: str) -> bool:
    db = sqlite3.connect('database.sqlite')
    cursor = db.cursor()
    
    sql = ('UPDATE chicken SET breed = ?, date = ?, level = ?, experience = ?, health = ?, strength = ?, defense = ?, hit_rate = ?, items = ? WHERE user_id = ?') # update user's chicken in database
    val = (name, date, level, exp, health, strength, defense, hit, items, user.id)
    
    cursor.execute(sql, val) # executes the instructions
    db.commit() # saves changes
    cursor.close()
    db.close()
    
    return True

def player_in_wild(user: hikari.User) -> None:
    if user in wild:
        return True
    return False

def get_cock_info(user: hikari.User) -> dict:
    db = sqlite3.connect('database.sqlite')
    cursor = db.cursor()
        
    cursor.execute(f'SELECT breed, date, health, strength, defense, hit_rate, level, experience, items FROM chicken WHERE user_id = {user.id}') # moves cursor to user's chicken info from database
    val = cursor.fetchone() # grabs the values of user's chicken
       
    try: # just in case for errors
        name = val[0] # name SHOULD be at index 0
        date = val[1] # date SHOULD be at index 1
        health = val[2] # health SHOULD be at index 2
        strength = val[3] # strength SHOULD be at index 3
        defense = val[4] # defense SHOULD be at index 4
        hit = val[5] # hit rate SHOULD be at index 5
        level = val[6] # level rate SHOULD be at index 6
        experience = val[7] # experience SHOULD be at index 7
        items = val[8] # items SHOULD be at index 8
    except:
        name = 'N/A'
        date = 'N/A'
        health = 0
        strength = 0
        defense = 0
        hit = 0
        level = 0
        experience = 0
        items = 'None'
    
    db.close
    cursor.close
    
    return {'name': name, 'date': date, 'level': level, 'experience': experience, 'health': health, 'strength': strength, 'defense': defense, 'hit': hit, 'items': items}

def generate_wild_cock(cock: str, userLvl: int, userHealth: int, userStrength: int, userDefense: int) -> dict:
    match cock:
        case 'Chick':
            level = userLvl
            health = round(userHealth * random.uniform(0.75, 1.25))
            strength = round(userStrength * random.uniform(0.75, 1.25))
            defense = round(userDefense * random.uniform(0.25, 0.50))
            hit = 60
        case 'Cockerel':
            level = userLvl
            health = round(userHealth * random.uniform(0.75, 1.25))
            strength = round(userStrength * random.uniform(0.75, 1.50))
            defense = round(userDefense * random.uniform(0.50, 0.75))
            hit = 70
        case 'Rooster':
            level = userLvl
            health = round(userHealth * random.uniform(0.90, 1.50))
            strength = round(userStrength * random.uniform(0.75, 1.50))
            defense = round(userDefense * random.uniform(0.50, 0.90))
            hit = 80
    
    return {'level': level, 'health': health, 'strength': strength, 'defense': defense, 'hit': hit}

def player_turn(turn: int) -> bool:
    if turn % 2 != 0:
        return True
    return False

def get_cock_damage(turn: int, userCock: dict, wildCock: dict) -> int:
    if player_turn(turn):
        return userCock.get('strength') - wildCock.get('defense') if (userCock.get('strength') - wildCock.get('defense')) > 0 else 0
    return wildCock.get('strength') - userCock.get('defense') if (wildCock.get('strength') - userCock.get('defense')) > 0 else 0

def item_loot_drop(user: hikari.User) -> str:
    itemList = ["Cat's Bell (+15❤️)", "Blazer Gloves (+3👊)", "Armguard (+2🛡️)", "Crusher's Belt (+2👊)", "Setzer's Coin (+5🎯)", "Death Skull (+3👊)", "Touph Ring (+1🛡️)", "Giant Haircomb (+1🛡️)", "White Ribbon (+2🛡️)", "Round Glasses (+1👊)", "Oni Mask (+3👊)", "Tengu Mask (+2👊)", "Bath Towel (+15❤️)", "Bear Hat (+10❤️)", "Moist Bread (+5❤️)", "Dragon Scale (+2🛡️)", "Spyglass (+5🎯)", "Pisces Shard (+15❤️)", "Coral Ring (+10❤️)", "Yogurt (+5❤️)", "Orange (+5❤️)", "Sweet Cookie (+5❤️)"]
    itemIndex = random.randint(0, len(itemList) - 1)
    
    db = sqlite3.connect('database.sqlite')
    cursor = db.cursor()
        
    cursor.execute(f'SELECT items FROM chicken WHERE user_id = {user.id}') # moves cursor to user's chicken info from database
    val = cursor.fetchone() # grabs the values of user's chicken experience
    
    try:
        items = val[0]
    except:
        items = 'None'
    
    if items == 'None':
        items = []
    else:
        items = list(items.split(', '))
    
    items.append(itemList[itemIndex])
    items = list(set(items))
    items = ', '.join(items)
    
    sql = ('UPDATE chicken SET items = ? WHERE user_id = ?')
    val = (items, user.id)
    
    cursor.execute(sql, val) # executes the instructions
    db.commit() # saves changes
    
    return itemList[itemIndex]

def items_to_list(list: str) -> list:
    return list.split(', ')

def add_item_to_stats(userCock: dict) -> dict:
    items = items_to_list(userCock.get('items'))
    for i in items:
        match i:
            case "Setzer's Coin (+5🎯)":
                userCock['hit'] = userCock['hit'] + 5
            case "Spyglass (+5🎯)":
                userCock['hit'] = userCock['hit'] + 5
            case "Pisces Shard (+15❤️)":
                userCock['health'] = userCock['health'] + 15
            case "Bath Towel (+15❤️)":
                userCock['health'] = userCock['health'] + 15
            case "Cat's Bell (+15❤️)":
                userCock['health'] = userCock['health'] + 15
            case "Bear Hat (+10❤️)":
                userCock['health'] = userCock['health'] + 10
            case "Coral Ring (+10❤️)":
                userCock['health'] = userCock['health'] + 10
            case "Moist Bread (+5❤️)":
                userCock['health'] = userCock['health'] + 5
            case "Yogurt (+5❤️)":
                userCock['health'] = userCock['health'] + 5
            case "Orange (+5❤️)":
                userCock['health'] = userCock['health'] + 5
            case "Sweet Cookie (+5❤️)":
                userCock['health'] = userCock['health'] + 5
            case "Oni Mask (+3👊)":
                userCock['strength'] = userCock['strength'] + 3
            case "Blazer Gloves (+3👊)":
                userCock['strength'] = userCock['strength'] + 3
            case "Death Skull (+3👊)":
                userCock['strength'] = userCock['strength'] + 3
            case "Crusher's Belt (+2👊)":
                userCock['strength'] = userCock['strength'] + 2
            case "Tengu Mask (+2👊)":
                userCock['strength'] = userCock['strength'] + 2
            case "Round Glasses (+1👊)":
                userCock['strength'] = userCock['strength'] + 1
            case "Armguard (+2🛡️)":
                userCock['defense'] = userCock['defense'] + 2
            case "White Ribbon (+2🛡️)":
                userCock['defense'] = userCock['defense'] + 2 
            case "Dragon Scale (+2🛡️)":
                userCock['defense'] = userCock['defense'] + 2
            case "Giant Haircomb (+1🛡️)":
                userCock['defense'] = userCock['defense'] + 1    
            case "Touph Ring (+1🛡️)":
                userCock['defense'] = userCock['defense'] + 1 
    return userCock

def add_exp(user: hikari.User, number: int) -> dict:
    db = sqlite3.connect('database.sqlite')
    cursor = db.cursor()
        
    cursor.execute(f'SELECT level, experience, health, strength, defense FROM chicken WHERE user_id = {user.id}') # moves cursor to user's chicken info from database
    val = cursor.fetchone() # grabs the values of user's chicken experienc
    
    try:
        level = val[0]
        experience = val[1]
        health = val[2]
        strength = val[3]
        defense = val[4]
    except:
        level = 0
        experience = 0
        health = 0
        strength = 0
        defense = 0
    
    levelUp = False
    healthVal = random.randint(10, 18)
    strengthVal = random.randint(1, 3)
    defenseVal = random.randint(0, 2)
        
    if experience + number >= 100 and level < 100:
        level = level + 1
        levelUp = True
        sql = ('UPDATE chicken SET level = ?, experience = ?, health = ?, strength = ?, defense = ? WHERE user_id = ?')
        val = (level, (experience + number) - 100, health + healthVal, strength + strengthVal, defense + defenseVal, user.id)
    elif experience + number <= 100:
        levelUp = False
        sql = ('UPDATE chicken SET experience = ? WHERE user_id = ?')
        val = (experience + number, user.id)
    else:
        levelUp = False
        sql = ('UPDATE chicken SET experience = ? WHERE user_id = ?')
        val = (100, user.id)
    
    cursor.execute(sql, val) # executes the instructions
    db.commit() # saves changes
    
    return {'level_up': levelUp, 'level': level, 'old_health': health, 'new_health': health + healthVal, 'old_strength': strength, 'new_strength': strength + strengthVal, 'old_defense': defense, 'new_defense': defense + defenseVal}

def reset_exp(user: hikari.User) -> None:
    db = sqlite3.connect('database.sqlite')
    cursor = db.cursor()
    
    sql = ('UPDATE chicken SET experience = ? WHERE user_id = ?')
    val = (0, user.id)
    
    cursor.execute(sql, val) # executes the instructions
    db.commit() # saves changes