import asyncio
import uuid
import hikari
import lightbulb
import miru
import requests

from bot import get_setting, verify_user, register_user
from utils.economy.manager import EconomyManager
from utils.economy.sovereignmc import SovManager

SERVER_IP = "sov.tuxbrain.org"
GUILD_ID = 1041100223574970468
CONSOLE_ID = 1161817326782521354
WEEKLY_LIMIT = 5000
CONVERT_RATE = 20

loader = lightbulb.Loader()
group = lightbulb.Group(name="sovereignmc", description="Commands for SovereignMC.")

economy = EconomyManager()
database = SovManager()

@loader.listener(hikari.StartedEvent)
async def on_start(event: hikari.StartedEvent, bot: hikari.GatewayBot) -> None:
    try:
        guild = await bot.rest.fetch_guild(GUILD_ID)
        if guild is not None:
            loader.command(group)
    except hikari.NotFoundError:
        await loader.command(group, guilds=[])

class CoinModal(lightbulb.components.Modal):
    def __init__(self) -> None:
        self.amount = self.add_short_text_input(label="Amount", placeholder="100", required=True)
        self.success = False
    
    async def on_submit(self, ctx: lightbulb.components.ModalContext) -> None:
        database.get_table()
        self.amount = (int(ctx.value_for(self.amount)) // CONVERT_RATE) * CONVERT_RATE
        coins = database.get_coins(ctx.user.id)

        if self.amount + coins > WEEKLY_LIMIT:
            self.amount = WEEKLY_LIMIT - coins

        if self.amount == 0 and coins == WEEKLY_LIMIT:
            embed = hikari.Embed(description=f"You have reached the weekly limit of {WEEKLY_LIMIT:,} 🪙.", color=get_setting("general", "embed_error_color"))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

        if self.amount < CONVERT_RATE:
            embed = hikari.Embed(description=f"The amount must be at least {CONVERT_RATE} 🪙.", color=get_setting("general", "embed_error_color"))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        self.success = True
        embed = hikari.Embed(description=f"You have successfully set your coin amount to {self.amount:,} 🪙.", color=get_setting("general", "embed_success_color")) 
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

class AccountModal(lightbulb.components.Modal):
    def __init__(self) -> None:
        self.username = self.add_short_text_input(label="Username", placeholder="PieTwelve", required=True)
        self.uuid = None
        self.success = False
    
    async def on_submit(self, ctx: lightbulb.components.ModalContext) -> None:
        self.username = ctx.value_for(self.username)
        url = f"https://api.mojang.com/users/profiles/minecraft/{self.username}"
        response = requests.get(url)
        self.uuid = response.json()["id"] if response.status_code == 200 else None
        self.username = response.json()["name"] if response.status_code == 200 else None

        if self.uuid is None:
            embed = hikari.Embed(description="This Minecraft account does not exist.", color=get_setting("general", "embed_error_color"))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

        self.success = True
        embed = hikari.Embed(description=f"You have successfully set your Minecraft account to **{self.username}**.", color=get_setting("general", "embed_success_color"))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

class ConvertMenu(lightbulb.components.Menu):
    def __init__(self, ctx: lightbulb.Context, embed: hikari.Embed) -> None:
        self.confirmButton = self.add_interactive_button(style=hikari.ButtonStyle.SUCCESS, label="Confirm", on_press=self.on_confirm)
        self.moneyButton = self.add_interactive_button(style=hikari.ButtonStyle.PRIMARY, emoji="🪙", label="Set Coins", on_press=self.set_money)
        self.accountButton = self.add_interactive_button(style=hikari.ButtonStyle.PRIMARY, emoji=hikari.Emoji.parse("<:minecraft:1316624654185791541>"), label="Set Coins", on_press=self.set_account)
        self.ctx = ctx
        self.embed = embed
        self.author = ctx.user
        self.amount = 0
        self.username = "N/A"

    async def on_confirm(self, ctx: lightbulb.components.MenuContext) -> None:
        url = f"https://api.mcsrvstat.us/simple/{SERVER_IP}"
        response = requests.get(url)
        online = True if response.status_code == 200 else False

        if not online:
            embed = hikari.Embed(description="The server is currently offline.", color=get_setting("general", "embed_error_color"))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        if self.amount == 0 or self.username == "N/A":
            embed = hikari.Embed(description="You must specify the coin amount and Minecraft account.", color=get_setting("general", "embed_error_color"))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

        if verify_user(ctx.user) is None:
            register_user(ctx.user)
        
        if economy.check_sufficient_amount(ctx.user.id, self.amount) == False:
            embed = hikari.Embed(description="You do not have enough money!", color=get_setting("general", "embed_error_color"))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

        try:
            await ctx.client.rest.create_message(CONSOLE_ID, f"eco add {self.username} {self.amount // CONVERT_RATE}")
            economy.remove_money(ctx.user.id, self.amount, True)
        except hikari.ForbiddenError:
            embed = hikari.Embed(description="Failed to add Gems SovereignMC. Please try again later.", color=get_setting("general", "embed_error_color"))
            return await ctx.respond(embed)

        database.get_table()
        database.set_coins(ctx.user.id, database.get_coins(ctx.user.id) + self.amount)
        
        embed = hikari.Embed(
            description = f"You have successfully converted {self.amount:,} 🪙 into {self.amount // CONVERT_RATE:,} Gem(s).", 
            color = get_setting("general", "embed_success_color")
        )

        await ctx.edit_response(self.embed, components=[])
        await ctx.respond(embed)

    async def set_money(self, ctx: lightbulb.components.MenuContext) -> None:
        modal = CoinModal()
        
        await ctx.respond_with_modal("Set Coin Amount", cid := str(uuid.uuid4()), components=modal)

        try:
            await modal.attach(ctx.client, cid, timeout=300)
        except asyncio.TimeoutError:
            pass
        
        if not modal.success:
            return

        self.amount = modal.amount
        self.embed.description = (
            f"You can convert coins into gems at a rate of **{CONVERT_RATE:,}** 🪙 per **1 Gem**. "
            f"There is a weekly limit of **{WEEKLY_LIMIT:,}** 🪙 that you can convert. "
            f"The limit resets every Monday. "
            f"To proceed, please specify your coin amount and Minecraft account.\n\n"
            f"> **Minecraft Account:** {self.username}\n"
            f"> **Coin Amount:** {self.amount:,} 🪙\n"
            f"> **Gem Amount:** {self.amount // CONVERT_RATE:,} Gem(s)"
        )

        await ctx.interaction.edit_initial_response(embed=self.embed, components=self)

    async def set_account(self, ctx: lightbulb.components.MenuContext) -> None:
        modal = AccountModal()
        
        await ctx.respond_with_modal("Set Minecraft Account", cid := str(uuid.uuid4()), components=modal)

        try:
            await modal.attach(ctx.client, cid, timeout=300)
        except asyncio.TimeoutError:
            pass

        if not modal.success:
            return
        
        self.username = modal.username
        self.embed.description = (
            f"You can convert coins into gems at a rate of **{CONVERT_RATE:,}** 🪙 per **1 Gem**. "
            f"There is a weekly limit of **{WEEKLY_LIMIT:,}** 🪙 that you can convert. "
            f"The limit resets every Monday. "
            f"To proceed, please specify your coin amount and Minecraft account.\n\n"
            f"> **Minecraft Account:** {self.username}\n"
            f"> **Coin Amount:** {self.amount:,} 🪙\n"
            f"> **Gem Amount:** {self.amount // CONVERT_RATE:,} Gem(s)"
        )
        self.embed.set_thumbnail(f"https://mc-heads.net/avatar/{modal.uuid}")

        await ctx.interaction.edit_initial_response(embed=self.embed, components=self)

    async def predicate(self, ctx: lightbulb.components.MenuContext) -> bool:
        return self.author.id == ctx.user.id

@group.register
class Convert(lightbulb.SlashCommand, name="convert", description="Convert coins into Gems."):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        if ctx.guild_id != GUILD_ID:
            embed = hikari.Embed(description="This command can only be used in the SovereignMC Discord server.", color=get_setting("general", "embed_error_color"))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

        embed = hikari.Embed(
            title = "SovereignMC: Coins to Gems Conversion",
            description = (
                f"You can convert coins into gems at a rate of **{CONVERT_RATE:,}** 🪙 per **1 Gem**. "
                f"There is a weekly limit of **{WEEKLY_LIMIT:,}** 🪙 that you can convert. "
                f"The limit resets every Monday. "
                f"To proceed, please specify your coin amount and Minecraft account.\n\n"
                f"> **Minecraft Account:** N/A\n"
                f"> **Coin Amount:** 0 🪙\n"
                f"> **Gem Amount:** 0 Gem(s)"
            ),
            color = get_setting("general", "embed_color")
        )

        menu = ConvertMenu(ctx, embed)
        resp = await ctx.respond(embed, components=menu)

        try:
            await menu.attach(ctx.client, timeout=300)
        except asyncio.TimeoutError:
            await ctx.edit_response(resp, components=[])