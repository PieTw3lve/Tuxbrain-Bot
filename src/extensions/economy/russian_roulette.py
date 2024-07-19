import hikari
import lightbulb
import miru
import random

from bot import get_setting, verify_user, register_user
from utils.economy.manager import EconomyManager

plugin = lightbulb.Plugin('Russian Roulette')
economy = EconomyManager()

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('bet', 'The amount players will bet.', type=int, min_value=100, max_value=None, required=True)
@lightbulb.option('capacity', 'How many bullet?', type=int, min_value=6, max_value=100, required=True)
@lightbulb.command('russian-roulette', 'Engage in a game of Russian Roulette with fellow Discord members.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def russian_roulette(ctx: lightbulb.Context, capacity: int, bet: int):
    if verify_user(ctx.user) == None: # if user has never been register
        register_user(ctx.user)
        
    if economy.remove_money(ctx.user.id, bet, False) == False: # if user has enough money
        embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    players = {f'<@{ctx.user.id}>': {'name': f'{ctx.user.global_name}', 'id': ctx.user.id, 'url': ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url}}
    
    embed = hikari.Embed(title=f'{ctx.user.global_name} has started a Russian Roulette game!', description='`DO NOT WORRY! YOU WILL NOT DIE IN REAL LIFE!\nYOU WILL ONLY HURT YOUR SELF ESTEEM!`', color=get_setting('general', 'embed_color'))
    embed.set_image('assets/img/fun/revolver.png')
    embed.add_field(name='__Game info__', value=f'Initial Bet: 🪙 {bet:,}\nBet Pool: 🪙 {bet:,}\nChamber Capacity: `{capacity:,}`', inline=True)
    embed.add_field(name='__Player List__', value=f'{", ".join(players)}', inline=True)
    embed.set_footer(text=f'The game will timeout in 2 minutes!')
    
    view = RRLobbyView(ctx.author, players, capacity, bet)
    
    await ctx.respond(embed, components=view.build())
    
    client = ctx.bot.d.get('client')
    client.start_view(view) # starts up lobby
    await view.wait() # waiting until lobby starts or timed out
    
    if not view.gameStart: # if lobby timed out
        return
    
    embed = hikari.Embed(title=f"It's {ctx.user.global_name} Turn!", description=f'Players: {", ".join(view.game["players"])}\nBet Pool: 🪙 {view.game["pool"]:,}\nBullets Remaining: `{view.game["capacity"]}`', color=get_setting('general', 'embed_color'))
    embed.set_image('assets/img/fun/revolver.png')
    embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
    embed.set_footer(text=f'You have {15.0} seconds to choose an action!')
        
    view = RRGameView(view.game, 15.0)
        
    await ctx.edit_last_response(embed, components=view.build())

    client.start_view(view) # starts game
    
class RRLobbyView(miru.View):
    def __init__(self, author: hikari.User, players: dict, capacity: int, amount: int) -> None:
        super().__init__(timeout=120.0)
        self.game = {'author': author, 'players': players, 'capacity': capacity, 'amount': amount, 'pool': amount}
        self.gameStart = False
    
    @miru.button(label='Start', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def start_game(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if self.game.get('author').id != ctx.user.id: # checks if user is host
            embed = hikari.Embed(description='You are not the host!', color=get_setting('general', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif len(self.game['players']) == 1:
            embed = hikari.Embed(description='You do not have enough players!', color=get_setting('general', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif self.game['pool'] % (len(self.game['players']) - 1) != 0:
            embed = hikari.Embed(description="Loser's bet cannot be distributed equally with the current amount of players!", color=get_setting('general', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        self.gameStart = True
        self.stop()
    
    @miru.button(label='Join Game', style=hikari.ButtonStyle.PRIMARY, row=1)
    async def join(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if verify_user(ctx.user) == None: # if user has never been register
            register_user(ctx.user)

        player = f'<@{ctx.user.id}>'
        playerInfo = {'name': f'{ctx.user.global_name}', 'id': ctx.user.id, 'url': ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url}
        
        if player in self.game['players']: # checks if user already joined
            embed = hikari.Embed(description='You already joined this game!', color=get_setting('general', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif economy.remove_money(ctx.user.id, self.game['amount'], False) == False: # if user has enough money
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return

        self.game['players'][player] = playerInfo
        self.game['pool'] = self.game['pool'] + self.game['amount']
        
        embed = hikari.Embed(title=f'{self.game["author"]} has started a Russian Roulette game!', description='`DO NOT WORRY! YOU WILL NOT DIE IN REAL LIFE!\nYOU WILL ONLY HURT YOUR SELF ESTEEM!`', color=get_setting('general', 'embed_color'))
        embed.set_image('assets/img/fun/revolver.png')
        embed.add_field(name='__Game info__', value=f"Initial Bet: 🪙 {self.game['amount']:,}\nBet Pool: 🪙 {self.game['pool']:,}\nChamber Capacity: `{self.game['capacity']:,}`", inline=True)
        embed.add_field(name='__Player List__', value=f'{", ".join(self.game["players"])}', inline=True)
        embed.set_footer(text=f'The game will timeout in 2 minutes!')
        
        await ctx.message.edit(embed)
        
    @miru.button(label='Refund', style=hikari.ButtonStyle.DANGER, row=1)
    async def refund(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if self.game['author'].id != ctx.user.id: # checks if user is host
            embed = hikari.Embed(description='You are not the host!', color=get_setting('general', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        for player in self.game['players'].values():
            economy.add_money(player['id'], self.game['amount'], False)
        
        embed = hikari.Embed(title=f"{self.game.get('author')} has refunded all bets!", description='`DO NOT WORRY! YOU WILL NOT DIE IN REAL LIFE!\nYOU WILL ONLY HURT YOUR SELF ESTEEM!`', color=get_setting('general', 'embed_color'))
        embed.set_image('assets/img/fun/revolver.png')
        embed.add_field(name='__Game info__', value=f"Initial Bet: 🪙 {self.game['amount']:,}\nBet Pool: 🪙 {self.game['pool']:,}\nChamber Capacity: `{self.game['capacity']:,}`", inline=True)
        embed.add_field(name='__Player List__', value=f'{", ".join(self.game["players"])}', inline=True)
        
        await ctx.edit_response(embed, components=[])
    
    async def on_timeout(self) -> None:
        for player in self.game['players'].values():
            economy.add_money(player['id'], self.game['amount'], False)
        
        embed = hikari.Embed(title=f"Game has timed out! All bets have been refunded!", color=get_setting('general', 'embed_color'))
        embed.set_image('assets/img/fun/revolver.png')
        embed.add_field(name='__Game info__', value=f"Initial Bet: 🪙 {self.game['amount']:,}\nBet Pool: 🪙 {self.game['pool']:,}\nChamber Capacity: `{self.game['capacity']:,}`", inline=True)
        embed.add_field(name='__Player List__', value=f'`{", ".join(self.game["players"])}`', inline=True)
        
        await self.message.edit(embed, components=[])
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return True

class RRGameView(miru.View):
    def __init__(self, game: dict, timeout: float) -> None:
        super().__init__(timeout=timeout)
        self.game = game
        self.playerIter = iter(game['players'].items())
        self.player = next(self.playerIter)[1]
        self.chamber = [True]
        self.gameMessages = ['Huh, there seems to be no bullet...', 'You got lucky this time!', "Beginner's luck!", 'You should end turn before it gets dangerous!', 'Sigh... No bullet this time.', 'You are safe, for now...', 'You lost! Just kidding, but it was close!', 'Nice flinch!']
        self.endTurn = False
        
        for i in range(self.game['capacity'] - 1):
            self.chamber.append(False)
        
        random.shuffle(self.chamber)
    
    @miru.button(label='Fire', emoji='💥', style=hikari.ButtonStyle.PRIMARY, row=1)
    async def fire(self, ctx: miru.ViewContext, button: miru.Button):
        if len(self.chamber) == 0:
            return
        elif self.chamber[0]:
            embed = hikari.Embed(title=f"Oh no! {self.player['name']} shot themselves!", description=f'`{self.player["name"]} bet has been distributed among the winners!`\n\nPlayers: {", ".join(self.game["players"])}\nBet Pool: 🪙 {self.game["pool"]:,}\nBullets Remaining: `{len(self.chamber) - 1}`', color=get_setting('general', 'embed_color'))
            embed.set_image('assets/img/fun/revolver.png')
            embed.set_thumbnail(self.player['url'])
            
            for player in self.game['players'].values(): 
                if player['id'] != self.player['id']: # check if player is not the loser
                    economy.add_money(player['id'], self.game['pool'] / (len(self.game['players']) - 1), False)
                    economy.add_gain(player['id'], self.game['amount'])
            economy.add_loss(self.player['id'], self.game['amount'])
            
            await ctx.edit_response(embed, components=[])
            self.stop()
            return
        
        self.chamber.pop(0) # removes bullet
        
        embed = hikari.Embed(title=f"It's {self.player['name']} Turn!", description=f'`{self.gameMessages[random.randint(0, len(self.gameMessages) - 1)]}`\n\nPlayers: {", ".join(self.game["players"])}\nBet Pool: 🪙 {self.game["pool"]:,}\nBullets Remaining: `{len(self.chamber)}`', color=get_setting('general', 'embed_color'))
        embed.set_image('assets/img/fun/revolver.png')
        embed.set_thumbnail(self.player['url'])
        embed.set_footer(text=f'You have {self.timeout} seconds to choose an action!')
        
        self.endTurn = True
        await ctx.edit_response(embed, components=self.build())
    
    @miru.button(label='End Turn', style=hikari.ButtonStyle.SUCCESS, row=1, disabled=False)
    async def next_turn(self, ctx: miru.ViewContext, button: miru.Button):
        if self.endTurn:
            try: # cycle turns
                self.player = next(self.playerIter)[1]
            except:
                self.playerIter = iter(self.game['players'].items())
                self.player = next(self.playerIter)[1]
        else:
            embed = hikari.Embed(description='You need to fire at least one shot!', color=get_setting('general', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        embed = hikari.Embed(title=f"It's {self.player['name']} Turn!", description=f'Players: {", ".join(self.game["players"])}\nBet Pool: 🪙 {self.game["pool"]:,}\nBullets Remaining: `{len(self.chamber)}`', color=get_setting('general', 'embed_color'))
        embed.set_image('assets/img/fun/revolver.png')
        embed.set_thumbnail(self.player['url'])
        embed.set_footer(text=f'You have {self.timeout} seconds to choose an action!')
        
        self.endTurn = False
        await ctx.edit_response(embed, components=self.build())
    
    async def on_timeout(self) -> None:
        embed = hikari.Embed(title=f"Oh no! {self.player['name']} took too long and the gun exploded!", description=f'`{self.player["name"]} bet has been distributed among the winners!`\n\nPlayers: {", ".join(self.game["players"])}\nBet Pool: 🪙 {self.game["pool"]:,}\nBullets Remaining: `{len(self.chamber) - 1}`', color=get_setting('general', 'embed_color'))
        embed.set_image('assets/img/fun/revolver.png')
        embed.set_thumbnail(self.player['url'])
        
        for player in self.game['players'].values(): 
            if player['id'] != self.player['id']: # check if player is not the loser
                economy.add_money(player['id'], self.game['pool'] / (len(self.game['players']) - 1), False)
                economy.add_gain(player['id'], self.game['amount'])
        economy.add_loss(self.player['id'], self.game['amount'])
            
        await self.message.edit(embed, components=[])
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.player['id']

def load(bot):
    bot.add_plugin(plugin)