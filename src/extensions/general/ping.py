import hikari
import lightbulb

from bot import get_setting

loader = lightbulb.Loader()

@loader.command
class Ping(lightbulb.SlashCommand, name="ping", description="Check the bot's latency."):
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, bot: hikari.GatewayBot) -> None:
        embed = (hikari.Embed(title="Pong!", description=f"{round(bot.heartbeat_latency * 1000)}ms 📶", color=get_setting("general", "embed_color")))
        await ctx.respond(embed)