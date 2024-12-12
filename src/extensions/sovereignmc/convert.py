import hikari
import lightbulb
import miru
import requests

from bot import get_setting, verify_user, register_user
from utils.economy.manager import EconomyManager
from utils.economy.sovereignmc import SovManager

SERVER_IP = 'sov.tuxbrain.org'
GUILD_ID = 924876440208564224
CONSOLE_ID = 1161817326782521354
WEEKLY_LIMIT = 6000
CONVERT_RATE = 25

plugin = lightbulb.Plugin('SovereignMC')
economy = EconomyManager()
database = SovManager()

@plugin.listener(hikari.StartedEvent)
async def on_start(event: hikari.StartedEvent) -> None:
    if plugin.bot.cache.get_guild(GUILD_ID) is None:
        plugin.bot.remove_plugin(plugin)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('sovereignmc', 'Commands for SovereignMC.')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def sovereignmc(ctx: lightbulb.Context) -> None:
    return

class CoinModal(miru.Modal, title='Set Coin Amount'):
    amount = miru.TextInput(label='Amount', placeholder='100', required=True)
    success = False

    async def callback(self, ctx: miru.ModalContext) -> None:
        database.create_table()
        self.amount = (int(self.amount.value) // CONVERT_RATE) * CONVERT_RATE
        coins = database.get_coins(ctx.author.id)

        if self.amount + coins > WEEKLY_LIMIT:
            self.amount = WEEKLY_LIMIT - coins

        if self.amount == 0:
            embed = hikari.Embed(description=f'You have reached the weekly limit of {WEEKLY_LIMIT:,} 🪙.', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

        if self.amount < CONVERT_RATE:
            embed = hikari.Embed(description=f'The amount must be at least {CONVERT_RATE} 🪙.', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        self.success = True
        embed = hikari.Embed(description=f'You have successfully set your coin amount to {self.amount:,} 🪙.', color=get_setting('general', 'embed_success_color')) 
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

class MinecraftModal(miru.Modal, title='Set Minecraft Account'):
    username = miru.TextInput(label='Username', placeholder='PieTwelve', required=True)
    uuid = None
    success = False

    async def callback(self, ctx: miru.ModalContext) -> None:
        url = f'https://api.mojang.com/users/profiles/minecraft/{self.username.value}'
        response = requests.get(url)
        self.uuid = response.json()['id'] if response.status_code == 200 else None

        if self.uuid is None:
            embed = hikari.Embed(description='This Minecraft account does not exist.', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

        self.success = True
        embed = hikari.Embed(description=f'You have successfully set your Minecraft account to **{self.username.value}**.', color=get_setting('general', 'embed_success_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

class ConvertView(miru.View):
    def __init__(self, ctx: lightbulb.Context, embed: hikari.Embed) -> None:
        super().__init__(timeout=300)
        self.ctx = ctx
        self.embed = embed
        self.author = ctx.author
        self.amount = 0
        self.username = 'N/A'
    
    @miru.button(label='Confirm', style=hikari.ButtonStyle.SUCCESS, custom_id='confirm')
    async def confirm(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        url = f'https://api.mcsrvstat.us/simple/{SERVER_IP}'
        response = requests.get(url)
        online = True if response.status_code == 200 else False

        if not online:
            embed = hikari.Embed(description='The server is currently offline.', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        if self.amount == 0 or self.username == 'N/A':
            embed = hikari.Embed(description='You must specify the coin amount and Minecraft account.', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

        if verify_user(ctx.user) is None:
            register_user(ctx.user)
        
        if economy.remove_money(ctx.author.id, self.amount, True) == False:
            embed = hikari.Embed(description='You do not have enough money!', color=get_setting('general', 'embed_error_color'))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

        database.create_table()
        database.set_coins(ctx.author.id, database.get_coins(ctx.author.id) + self.amount)

        embed = hikari.Embed(
            description = f'You have successfully converted {self.amount:,} 🪙 into {self.amount // CONVERT_RATE:,} Gem(s).', 
            color = get_setting('general', 'embed_success_color')
        )

        await plugin.bot.rest.create_message(CONSOLE_ID, f'eco add {self.username} {self.amount // CONVERT_RATE}')
        await ctx.edit_response(self.embed, components=[])
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    
    @miru.button(label='Set Coins', emoji='🪙', style=hikari.ButtonStyle.PRIMARY, custom_id='coins')
    async def set_coins(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        modal = CoinModal()
        await ctx.respond_with_modal(modal)
        await modal.wait()
        
        if not modal.success:
            return

        self.amount = modal.amount
        self.embed.description = (
            f'You can convert coins into gems at a rate of **{CONVERT_RATE:,}** 🪙 per **1 Gem**. '
            f'There is a weekly limit of {WEEKLY_LIMIT:,} 🪙 that you can convert. '
            f'The limit resets every Monday. '
            f'To proceed, please specify your coin amount and Minecraft account.\n\n'
            f'> **Minecraft Account:** {self.username}\n'
            f'> **Coin Amount:** {self.amount:,} 🪙\n'
            f'> **Gem Amount:** {self.amount // CONVERT_RATE:,} Gem(s)'
        )
        await self.ctx.edit_last_response(embed=self.embed, components=self.build())
    
    @miru.button(label='Set Account', emoji='<:minecraft:1316624654185791541>', style=hikari.ButtonStyle.PRIMARY, custom_id='account')
    async def set_account(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        modal = MinecraftModal()
        await ctx.respond_with_modal(modal)
        await modal.wait()

        if not modal.success:
            return
        
        self.username = modal.username.value
        self.embed.description = (
            f'You can convert coins into gems at a rate of **{CONVERT_RATE:,}** 🪙 per **1 Gem**. '
            f'There is a weekly limit of {WEEKLY_LIMIT:,} 🪙 that you can convert. '
            f'The limit resets every Monday. '
            f'To proceed, please specify your coin amount and Minecraft account.\n\n'
            f'> **Minecraft Account:** {self.username}\n'
            f'> **Coin Amount:** {self.amount:,} 🪙\n'
            f'> **Gem Amount:** {self.amount // CONVERT_RATE:,} Gem(s)'
        )
        self.embed.set_thumbnail(f'https://mc-heads.net/avatar/{modal.uuid}')
        await self.ctx.edit_last_response(embed=self.embed, components=self.build())
    
    async def on_timeout(self) -> None:
        await self.ctx.edit_last_response(embed=self.embed, components=[])

    async def view_check(self, ctx: miru.ViewContext) -> bool:
        return self.author.id == ctx.author.id

@sovereignmc.child
@lightbulb.command('convert', 'Convert coins into Gems.')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def convert(ctx: lightbulb.Context) -> None:
    embed = hikari.Embed(
        title = 'SovereignMC: Coins to Gems Conversion',
        description = (
            f'You can convert coins into gems at a rate of **{CONVERT_RATE:,}** 🪙 per **1 Gem**. '
            f'There is a weekly limit of {WEEKLY_LIMIT:,} 🪙 that you can convert. '
            f'The limit resets every Monday. '
            f'To proceed, please specify your coin amount and Minecraft account.\n\n'
            f'> **Minecraft Account:** N/A\n'
            f'> **Coin Amount:** 0 🪙\n'
            f'> **Gem Amount:** 0 Gem(s)'
        ),
        color = get_setting('general', 'embed_color')
    )

    view = ConvertView(ctx, embed)
    await ctx.respond(embed, components=view.build())
    client = ctx.bot.d.get('client')
    client.start_view(view)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)