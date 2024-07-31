import hikari
import lightbulb
import miru

from bot import get_setting
from utils.economy.manager import EconomyManager

plugin = lightbulb.Plugin('Connect 4')
economy = EconomyManager()

class Connect4:
    def __init__(self):
        self.board = []
        for i in range(6):
            self.board.append(['🔵'] * 7)
        self.currentPlayer = '1'
  
    def printBoard(self):
        embed = hikari.Embed(description='')
        for row in self.board:
            embed.description = f'{embed.description}\n{" ".join(row)}'
        return embed.description
  
    def makeMove(self, col):
        for i in range(5, -1, -1):
            if self.board[i][col] == '🔵':
                if self.currentPlayer == '1':
                    self.board[i][col] = '🔴'
                else:
                    self.board[i][col] = '🟡'
                return
  
    def hasWon(self, player):
        # check rows
        for row in self.board:
            for i in range(4):
                if row[i:i + 4] == [player] * 4:
                    return True
        # check columns
        for col in range(7):
            for i in range(3):
                if (
                    self.board[i][col] == player
                    and self.board[i + 1][col] == player
                    and self.board[i + 2][col] == player
                    and self.board[i + 3][col] == player
                ):
                    return True
        # check diagonals
        for row in range(3):
            for col in range(4):
                if (
                    self.board[row][col] == player
                    and self.board[row + 1][col + 1] == player
                    and self.board[row + 2][col + 2] == player
                    and self.board[row + 3][col + 3] == player
                ):
                    return True
                if (
                    self.board[row][6 - col] == player
                    and self.board[row + 1][5 - col] == player
                    and self.board[row + 2][4 - col] == player
                    and self.board[row + 3][3 - col] == player
                ):
                    return True
        return False

class Connect4DuelView(miru.View):
    def __init__(self, ctx: lightbulb.Context, opponent: hikari.User, bet: int) -> None:
        super().__init__(timeout=120.0)
        self.ctx = ctx
        self.author = ctx.author
        self.opponent = opponent
        self.bet = bet
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
            description=f'**{self.author}** has challenged **{self.opponent}** to a Connect 4 game!',
            color=get_setting('general', 'embed_color')
        )
        embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
        embed.add_field(name='__Game Info__', value=f'Win Condition: Bet: 🪙 {self.bet}')
        
        await ctx.edit_response(embed, components=[])
        self.stop()
    
    async def on_timeout(self) -> None:
        economy.add_money(self.author.id, self.bet, False)
        
        embed = hikari.Embed(
            title=f'The game request timed out!',
            description=f'**{self.author}** has challenged **{self.opponent}** to a Connect 4 game!',
            color=get_setting('general', 'embed_color')
        )
        embed.set_thumbnail(self.author.avatar_url)
        embed.add_field(name='__Game Info__', value=f'Bet: 🪙 {self.bet}')
        
        await self.ctx.edit_last_response(embed, components=[])
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return ctx.user.id == self.opponent.id

class Connect4GameView(miru.View):
    def __init__(self, ctx: lightbulb.Context, game: Connect4, embed: hikari.Embed, opponent: hikari.User, bet: int) -> None:
        super().__init__(timeout=None)
        self.ctx = ctx
        self.game = game
        self.embed = embed
        self.author = ctx.author
        self.opponent = opponent
        self.bet = bet
    
    @miru.text_select(
        custom_id='column_select',
        placeholder='Select a Column',
        options=[
            miru.SelectOption(label='1', value='1'),
            miru.SelectOption(label='2', value='2'),
            miru.SelectOption(label='3', value='3'),
            miru.SelectOption(label='4', value='4'),
            miru.SelectOption(label='5', value='5'),
            miru.SelectOption(label='6', value='6'),
            miru.SelectOption(label='7', value='7'),
        ],
        row=1
    )
    async def select_column(self, ctx: miru.ViewContext, select: miru.TextSelect) -> None:
        move = int(select.values[0]) - 1
        player = '🔴' if self.game.currentPlayer == '1' else '🟡'
        
        if move < 0 or move > 6 or self.game.board[0][move] != '🔵':
            await ctx.respond(hikari.Embed(description='Invalid move, try again.', color=get_setting('general', 'embed_error_color')), flags=hikari.MessageFlag.EPHEMERAL)
            move = int(select.values[0]) - 1
            return
        self.game.makeMove(move)
        
        if self.game.hasWon(player):
            if self.game.currentPlayer == '1':
                self.embed.description = f'**{self.author.global_name}** wins!\n{self.game.printBoard()}'
                self.embed.set_thumbnail(self.author.avatar_url if self.author.avatar_url != None else self.author.default_avatar_url)
                economy.add_money(self.author.id, self.bet*2, False)
                economy.add_gain(self.author.id, self.bet)
                economy.add_loss(self.opponent.id, self.bet)
            else:
                self.embed.description = f'**{self.opponent.global_name}** wins!\n{self.game.printBoard()}'
                self.embed.set_thumbnail(self.opponent.avatar_url if self.opponent.avatar_url != None else self.opponent.default_avatar_url)
                economy.add_money(self.opponent.id, self.bet*2, False)
                economy.add_gain(self.opponent.id, self.bet)
                economy.add_loss(self.author.id, self.bet)
            self.embed.set_footer(None)
            await ctx.edit_response(self.embed, components=[])
            self.stop()
            return
        
        if self.game.currentPlayer == '1':
            self.game.currentPlayer = '2'
            self.embed.description = f"It's **{self.opponent.global_name}** turn! Make your move!\n{self.game.printBoard()}"
            self.embed.set_thumbnail(self.opponent.avatar_url if self.opponent.avatar_url != None else ctx.user.default_avatar_url)
        else:
            self.game.currentPlayer = '1'
            self.embed.description = f"It's **{self.author.global_name}** turn! Make your move!\n{self.game.printBoard()}"
            self.embed.set_thumbnail(self.author.avatar_url if self.author.avatar_url != None else ctx.user.default_avatar_url)
        
        await ctx.edit_response(self.embed)

    async def on_timeout(self) -> None:
        if self.game.currentPlayer == '1':
            self.embed.description = f'**{self.author.global_name}** wins!\n{self.game.printBoard()}'
            self.embed.set_thumbnail(self.author.avatar_url if self.author.avatar_url != None else self.author.default_avatar_url)
            economy.add_money(self.author.id, self.bet*2, False)
            economy.add_gain(self.author.id, self.bet)
            economy.add_loss(self.opponent.id, self.bet)
        else:
            self.embed.description = f'**{self.opponent.global_name}** wins!\n{self.game.printBoard()}'
            self.embed.set_thumbnail(self.opponent.avatar_url if self.opponent.avatar_url != None else self.opponent.default_avatar_url)
            economy.add_money(self.opponent.id, self.bet*2, False)
            economy.add_gain(self.opponent.id, self.bet)
            economy.add_loss(self.author.id, self.bet)
        self.embed.set_footer(None)
        await self.ctx.edit_last_response(self.embed, components=[])
        self.stop()
    
    async def view_check(self, ctx: miru.ViewContext) -> bool:
        if self.game.currentPlayer == '1':
            return ctx.user.id == self.author.id
        else:
            return ctx.user.id == self.opponent.id

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('bet', 'Number of coins you want to bet.', type=int, min_value=0, max_value=2000, required=True)
@lightbulb.option('user', 'The user to play against.', hikari.User, required=True)
@lightbulb.command('connect4', 'Engage in a Connect Four game with fellow Discord users.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def connect4(ctx: lightbulb.Context, user: hikari.User, bet: int) -> None:
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
        description=f'**{ctx.author}** has challenged **{user}** to a Connect Four game!',
        color=get_setting('general', 'embed_color')
    )
    embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
    embed.add_field(name='__Game Info__', value=f'Bet: 🪙 {bet}')
    embed.set_footer('The duel request will timeout in 2 minutes!')
    
    view = Connect4DuelView(ctx, user, bet)
    
    await ctx.respond(embed, components=view.build())
    
    client = ctx.bot.d.get('client')
    client.start_view(view)
    await view.wait()
    
    if not view.accepted:
        return
    
    game = Connect4()
    
    embed = hikari.Embed(title='Welcome to a game of Connect Four!', description=f"It's **{ctx.author.global_name}** turn! Make your move!\n{game.printBoard()}", color=get_setting('general', 'embed_color'))
    embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
    embed.set_footer('You have 60 seconds to choose an option or you will automatically forfeit!')

    view = Connect4GameView(ctx, game, embed, user, bet)
    
    await ctx.edit_last_response(embed, components=view.build())
    
    client = ctx.bot.d.get('client')
    client.start_view(view)

def load(bot):
    bot.add_plugin(plugin)