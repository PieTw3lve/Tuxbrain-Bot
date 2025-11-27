import asyncio
import hikari
import lightbulb

from bot import get_setting

VERSION = get_setting("bot", "version")

loader = lightbulb.Loader()

class InfoMenu(lightbulb.components.Menu):
    def __init__(self) -> None:
        self.select = self.add_text_select(
            placeholder="Choose a category",
            options=[
                lightbulb.components.TextSelectOption(emoji="📰", label="What's New", description="Explore our latest changes and bug fixes.", value=0),
                lightbulb.components.TextSelectOption(emoji="💬", label="About", description="More info about Tuxbrain Bot.", value=1),
                lightbulb.components.TextSelectOption(emoji="🤖", label="Invite Bot", description="How do I invite Tuxbrain Bot to my server?", value=2),
            ],
            on_select=self.on_select,
        )
    
    async def on_select(self, ctx: lightbulb.components.MenuContext) -> None:
        option = int(ctx.selected_values_for(self.select)[0])

        match option:
            case 0:
                embed = hikari.Embed(color=get_setting("general", "embed_color")) 
                embed.title = "📰 What's New"
                embed.description = f"Check out the latest changes and bug fixes [here](https://github.com/PieTw3lve/Tuxbrain-Bot/releases/tag/v{VERSION})."
                return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            case 1:
                embed = hikari.Embed(color=get_setting("general", "embed_color")) 
                author = await ctx.client.rest.fetch_user(291001658362560513)
                embed.title = "💬 About"
                embed.description = "Tuxbrain Bot is an [open source](https://github.com/PieTw3lve/Tux_Bot), multi-use Discord bot written in [hikari.py](https://www.hikari-py.dev/), a new static-typed Python API wrapper. " \
                                    f"It is programmed by <@{author.id}> to serve as the official Tuxbrain.org Discord bot. The bot is currently still in development, so there may be some bugs. " \
                                    "Although it was designed for Tuxbrain.org servers, the bot can be hosted and used on any server."
                embed.set_thumbnail(author.display_avatar_url)
                embed.add_field(name="Additional sources:", value="Profile and Rushsite designs - <@265992381780721675>\nRushsite data - <@353620712436531205>", inline=False)
                embed.add_field(name="Find any bugs?", value="If any bugs are encountered, please submit them on [Github](https://github.com/PieTw3lve/Tuxbrain-Bot/issues).", inline=False)
                return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            case 2:
                embed = hikari.Embed(color=get_setting("general", "embed_color")) 
                embed.title = "🤖 Invite Bot"
                embed.description = "Tuxbrain Bot is not currently available for direct invite to personal servers, but can be hosted locally by downloading from [Github](https://github.com/PieTw3lve/Tux_Bot). Instructions for hosting Tuxbrain Bot can be found on the GitHub repository."
                return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    
    async def predicate(self, ctx: lightbulb.components.MenuContext) -> bool:
        return True

@loader.command
class Ping(lightbulb.SlashCommand, name="help", description="Access additional information and commands."):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, bot: hikari.GatewayBot) -> None:
        botMember = bot.cache.get_member(ctx.guild_id, bot.get_me())
        menu = InfoMenu()
        
        embed = (hikari.Embed(title=f"{botMember.display_name}  `v{VERSION}`", description="I am a simple and humble bot that can do really cool things!", color=get_setting("general", "embed_color"))
            .set_thumbnail(botMember.display_avatar_url if botMember.display_avatar_url else botMember.default_avatar_url)
            .add_field("I have various cool features:", "• Moderation Integration\n• Economy Integration\n• SovereignMC Integration\n• Profile Customization\n• Music Player\n• Graphical Interfaces\n• Fun Interactive Games\n• And Many More!", inline=True)
            .add_field("Want to learn more about Tuxbrain Bot?", "\n\nClick on 💬 **About** to learn more about Tuxbrain Bot!\n\n**Want to learn more about commands?**\nAll commands are located in the dropdown menu.", inline=True)
            .set_footer("Use the select menu below for more info!")
        )
        
        resp = await ctx.respond(embed, components=menu)

        try:
            await menu.attach(ctx.client, timeout=60)
        except asyncio.TimeoutError:
            await ctx.edit_response(resp, components=[])