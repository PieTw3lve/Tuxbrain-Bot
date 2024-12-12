import hikari
import lightbulb
import miru

from bot import get_setting
from utils.economy.manager import EconomyManager

plugin = lightbulb.Plugin('RPS')
economy = EconomyManager()

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('wins', 'How many wins does a player need to win.', type=int, min_value=1, max_value=10, required=True)
@lightbulb.option('bet', 'Number of coins you want to bet.', type=int, min_value=0, max_value=2000, required=True)
@lightbulb.option('user', 'The user to play against.', hikari.User, required=True)
@lightbulb.command('rps', 'Challenge a Discord member to a game of Rock-Paper-Scissors.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def rps(ctx: lightbulb.Context, user: hikari.User, bet: int, wins: int) -> None:
    if user.is_bot or ctx.author.id == user.id: # checks if the user is a bot or the sender
        embed = hikari.Embed(description='You are not allowed to challenge this user!', color=get_setting('general', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif economy.remove_money(ctx.author.id, bet, False) == False:
        embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    embed = hikari.Embed(
        title=f'A wild duel request appeared!',
        description=f'**{ctx.author}** has challenged **{user}** to a RPS duel!',
        color=get_setting('general', 'embed_color')
    )
    embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
    embed.add_field(name='__Game Info__', value=f'Win Condition: First to `{wins}`!\nBet: 🪙 {bet}')
    embed.set_footer('The duel request will timeout in 5 minutes!')
    
    view = DuelView(ctx, user, bet, wins)
    
    await ctx.respond(embed, components=view.build())
    
    client = ctx.bot.d.get('client')
    client.start_view(view)
    await view.wait()
    
    if not view.accepted:
        return
    
    embed = hikari.Embed(
        title=f"It's Time to D-D-D-D-D-D DUEL!",
        description=f'Winner will receive 🪙 {bet*2}!',
        color=get_setting('general', 'embed_color')
    )
    embed.set_thumbnail('assets/img/fun/rps.png')
    embed.add_field(name=f'{ctx.author} [0]', value='❔', inline=False)
    embed.add_field(name=f'{user} [0]', value='❔', inline=False)
    embed.set_footer('You have 60 seconds to choose an action or you will automatically forfeit!')
    
    view = RPSGameView(embed, ctx.author, user, bet, wins)
    
    await ctx.edit_last_response(embed, components=view.build())
    
    client = ctx.bot.d.get('client')
    client.start_view(view)
    await view.wait()
    
    if view.player1['score'] > view.player2['score']:
        economy.add_loss(user.id, bet)
        economy.add_money(ctx.author.id, bet*2, False)
        economy.add_gain(ctx.author.id, bet)
        
        embed.title = f'{ctx.author} wins the RPS duel!'
        embed.description = f'🪙 {bet*2} coins has been sent to the winner!'
        embed.set_footer(text='')
        
        await ctx.edit_last_response(embed, components=[])
    elif view.player1['score'] < view.player2['score']:
        economy.add_loss(ctx.author.id, bet)
        economy.add_money(user.id, bet*2, False)
        economy.add_gain(user.id, bet)
        
        embed.title = f'{user} wins the RPS duel!'
        embed.description = f'🪙 {bet*2} coins has been sent to the winner!'
        embed.set_footer(text='')
        
        await ctx.edit_last_response(embed, components=[])
    else:
        economy.add_money(ctx.author.id, bet, False)
        economy.add_money(user.id, bet, False)
        
        embed.title = f'The RPS duel ends in a tie!'
        embed.description = f'Both players were refunded!'
        embed.set_footer(text='')
        
        await ctx.edit_last_response(embed, components=[])
    
class DuelView(miru.View):
    def __init__(self, ctx: lightbulb.Context, opponent: hikari.User, bet: int, wins: int) -> None:
        super().__init__(timeout=300.0, autodefer=True)
        self.ctx = ctx
        self.author = ctx.author
        self.opponent = opponent
        self.bet = bet
        self.wins = wins
        self.accepted = False

    @miru.button(label='Accept', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def accept(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if economy.remove_money(self.opponent.id, self.bet, False) == False:
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
    
        self.accepted = True
        self.stop()
    
    @miru.button(label='Decline', style=hikari.ButtonStyle.DANGER, row=1)
    async def decline(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        economy.add_money(self.author.id, self.bet, False)
        
        embed = hikari.Embed(
            title=f'{self.opponent} has declined the duel request!',
            description=f'**{self.author}** has challenged **{self.opponent}** to a RPS duel!',
            color=get_setting('general', 'embed_color')
        )
        embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
        embed.add_field(name='__Game Info__', value=f'Win Condition: First to `{self.wins}`!\nBet: 🪙 {self.bet}')
        
        await ctx.edit_response(embed, components=[])
        self.stop()
    
    async def on_timeout(self) -> None:
        economy.add_money(self.author.id, self.bet, False)
        
        embed = hikari.Embed(
            title=f'The duel request timed out!',
            description=f'**{self.author}** has challenged **{self.opponent}** to a RPS duel!',
            color=get_setting('general', 'embed_color')
        )
        embed.set_thumbnail(self.author.avatar_url)
        embed.add_field(name='__Game Info__', value=f'Win Condition: First to `{self.wins}`!\nBet: 🪙 {self.bet}')
        
        await self.ctx.edit_last_response(embed, components=[])
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.opponent.id

class RPSGameView(miru.View):
    def __init__(self, embed: hikari.Embed, author: hikari.User, opponent: hikari.User, bet: int, wins: int) -> None:
        super().__init__(timeout=60.0, autodefer=True)
        self.embed = embed
        self.author = author
        self.opponent = opponent
        self.bet = bet
        self.wins = wins
        self.turn = 1
        
        self.player1 = {'ready': False, 'score': 0, 'actions': []}
        self.player2 = {'ready': False, 'score': 0, 'actions': []}
    
    @miru.button(label='Rock', emoji='🪨', style=hikari.ButtonStyle.SECONDARY, row=1)
    async def rock(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if ctx.user.id == self.author.id:
            if not self.player1['ready']:
                self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}] ☑️', '❔' if len(self.player1['actions']) < 1 else ' | '.join(self.player1['actions']))
                await ctx.edit_response(self.embed)
                
                self.player1['ready'] = True
                self.player1['actions'].append('🪨')
            else:
                embed = hikari.Embed(description='You already chose an action!', color=get_setting('general', 'embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
        elif ctx.user.id == self.opponent.id:
            if not self.player2['ready']:
                self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}] ☑️', '❔' if len(self.player2['actions']) < 1 else ' | '.join(self.player2['actions']))
                await ctx.edit_response(self.embed)
                
                self.player2['ready'] = True
                self.player2['actions'].append('🪨')
            else:
                embed = hikari.Embed(description='You already chose an action!', color=get_setting('general', 'embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
        
        # Once everyone chose an action #
        
        if self.player1['ready'] and self.player2['ready']:
            match rps_get_result(self.player1['actions'], self.player2['actions'], self.turn):
                case 'Player1':
                    self.player1['score'] = self.player1['score'] + 1
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ✅'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ❌'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))
                case 'Player2':
                    self.player2['score'] = self.player2['score'] + 1
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ❌'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ✅'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))       
                case 'Tie':
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ✏️'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ✏️'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))

            if self.player1['score'] == self.wins or self.player2['score'] == self.wins:       
                self.stop()
                return
            
            self.player1['ready'] = False
            self.player2['ready'] = False
            
            self.turn = self.turn + 1
            
            await ctx.edit_response(self.embed)

    @miru.button(label='Paper', emoji='📄', style=hikari.ButtonStyle.SECONDARY, row=1)
    async def paper(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if ctx.user.id == self.author.id:
            if not self.player1['ready']:
                self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}] ☑️', '❔' if len(self.player1['actions']) < 1 else ' | '.join(self.player1['actions']))
                await ctx.edit_response(self.embed)
                
                self.player1['ready'] = True
                self.player1['actions'].append('📄')
            else:
                embed = hikari.Embed(description='You already chose an action!', color=get_setting('general', 'embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
        elif ctx.user.id == self.opponent.id:
            if not self.player2['ready']:
                self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}] ☑️', '❔' if len(self.player2['actions']) < 1 else ' | '.join(self.player2['actions']))
                await ctx.edit_response(self.embed)
                
                self.player2['ready'] = True
                self.player2['actions'].append('📄')
            else:
                embed = hikari.Embed(description='You already chose an action!', color=get_setting('general', 'embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
        
        # Once everyone chose an action #
        
        if self.player1['ready'] and self.player2['ready']:
            match rps_get_result(self.player1['actions'], self.player2['actions'], self.turn):
                case 'Player1':
                    self.player1['score'] = self.player1['score'] + 1
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ✅'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ❌'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))
                case 'Player2':
                    self.player2['score'] = self.player2['score'] + 1
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ❌'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ✅'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))       
                case 'Tie':
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ✏️'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ✏️'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))

            if self.player1['score'] == self.wins or self.player2['score'] == self.wins:
                self.stop()
                return
            
            self.player1['ready'] = False
            self.player2['ready'] = False
            
            self.turn = self.turn + 1
            
            await ctx.edit_response(self.embed)
        
    @miru.button(label='Scissors', emoji='✂️', style=hikari.ButtonStyle.SECONDARY, row=1)
    async def scissors(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        if ctx.user.id == self.author.id:
            if not self.player1['ready']:
                self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}] ☑️', '❔' if len(self.player1['actions']) < 1 else ' | '.join(self.player1['actions']))
                await ctx.edit_response(self.embed)
                
                self.player1['ready'] = True
                self.player1['actions'].append('✂️')
            else:
                embed = hikari.Embed(description='You already chose an action!', color=get_setting('general', 'embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
        elif ctx.user.id == self.opponent.id:
            if not self.player2['ready']:
                self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}] ☑️', '❔' if len(self.player2['actions']) < 1 else ' | '.join(self.player2['actions']))
                await ctx.edit_response(self.embed)
                
                self.player2['ready'] = True
                self.player2['actions'].append('✂️')
            else:
                embed = hikari.Embed(description='You already chose an action!', color=get_setting('general', 'embed_error_color'))
                await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
                return
        
        # Once everyone chose an action #
        
        if self.player1['ready'] and self.player2['ready']:
            match rps_get_result(self.player1['actions'], self.player2['actions'], self.turn):
                case 'Player1':
                    self.player1['score'] = self.player1['score'] + 1
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ✅'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ❌'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))
                case 'Player2':
                    self.player2['score'] = self.player2['score'] + 1
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ❌'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ✅'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))       
                case 'Tie':
                    self.player1['actions'][self.turn-1] = f'{self.player1["actions"][self.turn-1]} ✏️'
                    self.player2['actions'][self.turn-1] = f'{self.player2["actions"][self.turn-1]} ✏️'
                            
                    self.embed.edit_field(0, f'{self.author} [{self.player1["score"]}]', ' | '.join(self.player1["actions"]))
                    self.embed.edit_field(1, f'{self.opponent} [{self.player2["score"]}]', ' | '.join(self.player2["actions"]))

            if self.player1['score'] == self.wins or self.player2['score'] == self.wins:
                self.stop()
                return
            
            self.player1['ready'] = False
            self.player2['ready'] = False
            
            self.turn = self.turn + 1
            
            await ctx.edit_response(self.embed)
    
    async def on_timeout(self) -> None:
        if not self.player1['ready'] and not self.player2['ready']:
            self.stop()
        elif not self.player1['ready']:
            self.player2['score'] = self.wins
            self.stop()
        else:
            self.player1['score'] = self.wins
            self.stop()
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.opponent.id or self.author.id

def rps_get_result(player1Actions: list, player2Actions: list, turn: int) -> str:
    if player1Actions[turn-1] == player2Actions[turn-1]:
        return 'Tie'
    elif player1Actions[turn-1] == '🪨' and player2Actions[turn-1] == '✂️':
        return 'Player1'
    elif player1Actions[turn-1] == '📄' and player2Actions[turn-1] == '🪨':
        return 'Player1'
    elif player1Actions[turn-1] == '✂️' and player2Actions[turn-1] == '📄':
        return 'Player1'
    else:
        return 'Player2'
    
def load(bot):
    bot.add_plugin(plugin)