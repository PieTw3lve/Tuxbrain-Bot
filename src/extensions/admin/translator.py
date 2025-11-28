import hikari
import lightbulb
import json

from typing import Sequence
from deep_translator import GoogleTranslator
from lingua import Language, LanguageDetectorBuilder

from bot import get_setting, write_setting

loader = lightbulb.Loader()
group = lightbulb.Group(name="translator", description="Manage message translation detection settings.", default_member_permissions=hikari.Permissions.MANAGE_CHANNELS)

@loader.listener(hikari.GuildLeaveEvent)
async def remove_webhooks(event: hikari.GuildLeaveEvent) -> None:
    channels: Sequence[hikari.GuildChannel] = event.app.rest.fetch_guild_channels(event.guild_id)
    for channel in channels:
        if channel.type == 0:
            webhooks = await event.app.rest.fetch_channel_webhooks(channel.id)
            translators = get_translators(webhooks)
            if len(translators) > 0:
                translator = translators[0]
                await event.app.rest.delete_webhook(translator)
        
@loader.listener(hikari.MessageCreateEvent)
async def print_translation(event: hikari.MessageCreateEvent) -> None:
    translator = get_translators(await event.app.rest.fetch_channel_webhooks(event.channel_id))
    if len(translator) > 0:
        if event.is_bot or not event.content:
            return
        
        text = event.content
        detector = LanguageDetectorBuilder.from_all_languages().with_minimum_relative_distance(get_setting("general", "auto_translate_min_relative_distance")).build()
        language = detector.detect_language_of(text)
        confidence = detector.compute_language_confidence(text, language)

        if language != Language.ENGLISH and confidence > get_setting("general", "auto_translate_conf") and get_lang(language.name) != "Language not found":
            translation = GoogleTranslator(source=get_lang(language.name), target="en").translate(text)
            translator = await event.app.rest.create_webhook(channel=event.channel_id, name="Translating")
            await event.app.rest.execute_webhook(webhook=translator, token=translator.token, content=translation, username=f"{event.message.member.display_name} ({language.name.lower()})", avatar_url=event.message.member.display_avatar_url if event.message.member.display_avatar_url else event.message.member.default_avatar_url)
            await event.app.rest.delete_webhook(webhook=translator)

@group.register
class Info(lightbulb.SlashCommand, name="info", description="Get information about the automated message translation detection."):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, bot: hikari.GatewayBot) -> None:
        webhooks = await bot.rest.fetch_guild_webhooks(ctx.guild_id)
        translators = get_translators(webhooks)
        embed = hikari.Embed(title="Translator Settings", color=get_setting("general", "embed_color"))
        embed.add_field(name="Confidence Threshold", value=f"- Default: 0.8\n- Current: {get_setting('general', 'auto_translate_conf')}", inline=True)
        embed.add_field(name="Minimum Relative Distance", value=f"- Default: 0.9\n- Current: {get_setting('general', 'auto_translate_min_relative_distance')}", inline=True)
        embed.add_field(name="Active Channels", value=", ".join([f"<#{translator.channel_id}>" for translator in translators]) if translators else "No active channels.", inline=False)
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@group.register
class Enable(lightbulb.SlashCommand, name="enable", description="Activate automated message translation for this channel."):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, bot: hikari.GatewayBot) -> None:
        webhooks = await bot.rest.fetch_channel_webhooks(ctx.channel_id)
        translators = get_translators(webhooks)
        if len(translators) > 0:
            embed = hikari.Embed(description=f"Automated message translation is currently active in <#{ctx.channel_id}> channel.", color=get_setting("general", "embed_error_color"))
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        embed = hikari.Embed(description=f"Automated message translation has been activated for <#{ctx.channel_id}> channel.", color=get_setting("general", "embed_color"))
        await bot.rest.create_webhook(channel=ctx.channel_id, name="Translator", avatar=bot.get_me().display_avatar_url)
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@group.register
class Disable(lightbulb.SlashCommand, name="disable", description="Deactivate automated message translation for this channel."):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, bot: hikari.GatewayBot) -> None:
        webhooks = await bot.rest.fetch_channel_webhooks(ctx.channel_id)
        translators = get_translators(webhooks)
        if len(translators) > 0:
            translator = translators[0]
            embed = hikari.Embed(description=f"Automated message translation has been successfully deactivated in <#{ctx.channel_id}> channel.", color=get_setting("general", "embed_color"))
            await bot.rest.delete_webhook(translator)
            return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        embed = hikari.Embed(description=f"Automated message translation is currently inactive for the <#{ctx.channel_id}> channel.", color=get_setting("general", "embed_error_color"))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@group.register
class Settings(lightbulb.SlashCommand, name="settings", description="Manage automated message translation detection settings."):
    confidence: float = lightbulb.number("confidence", "1.0 means absolute confidence; 0.0 means no confidence. (default: 0.80)", min_value=0.0, max_value=1.0)
    minimumRelativeDistance: float = lightbulb.number("minimum-relative-distance", "0.99 means high distinction; 0.0 allows close probabilities for predictions (default: 0.90).", min_value=0.0, max_value=0.99)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, bot: hikari.GatewayBot) -> None:
        try:
            write_setting("settings", "auto_translate_conf", round(self.confidence, 2))
            write_setting("settings", "auto_translate_min_relative_distance", round(self.minimumRelativeDistance, 2))
            embed = hikari.Embed(description=f"Automated message translation confidence has been set to {round(self.confidence, 2)} and minimum relative distance has been set to {round(self.minimumRelativeDistance, 2)}.", color=get_setting("general", "embed_color"))
        except:
            embed = hikari.Embed(description=f"Failed to set automated message translation detection settings!", color=get_setting("general", "embed_error_color"))
        
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def get_lang(lang: str):
    with open("assets/json/language.json", "r") as openfile:
        data = json.load(openfile)
        for item in data.items():
            if item[1] == lang:
                return item[0]
        return "Language not found"

def get_translators(webhooks: Sequence[hikari.PartialWebhook]) -> Sequence[hikari.PartialWebhook]:
    translators = []
    for webhook in webhooks:
        if webhook.name == "Translator":
            translators.append(webhook)
    return translators

loader.command(group)