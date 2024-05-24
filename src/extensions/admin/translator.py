import hikari
import lightbulb
import json

from typing import Sequence
from deep_translator import GoogleTranslator
from lingua import Language, LanguageDetectorBuilder

from bot import get_setting, write_setting

plugin = lightbulb.Plugin('Translator')

@plugin.listener(hikari.GuildLeaveEvent)
async def remove_webhooks(event: hikari.GuildLeaveEvent) -> None:
    channels = event.app.rest.fetch_guild_channels(event.guild_id)
    for channel in channels:
        if channel.type == 0:
            webhooks = await event.app.rest.fetch_channel_webhooks(channel.id)
            translators = get_translators(webhooks)
            if len(translators) > 0:
                translator = translators[0]
                await event.app.rest.delete_webhook(translator)
        
@plugin.listener(hikari.MessageCreateEvent)
async def print_translation(event: hikari.MessageCreateEvent) -> None:
    translator = get_translators(await event.app.rest.fetch_channel_webhooks(event.channel_id))
    if len(translator) > 0:
        if event.is_bot or not event.content:
            return
        
        text = event.content
        detector = LanguageDetectorBuilder.from_all_languages().with_minimum_relative_distance(get_setting('settings', 'auto_translate_min_relative_distance')).build()
        language = detector.detect_language_of(text)
        confidence = detector.compute_language_confidence(text, language)

        if language != Language.ENGLISH and confidence > get_setting('settings', 'auto_translate_conf') and get_lang(language.name) != 'Language not found':
            translation = GoogleTranslator(source=get_lang(language.name), target='en').translate(text)
            translator = await event.app.rest.create_webhook(channel=event.channel_id, name='Translating')
            await event.app.rest.execute_webhook(webhook=translator, token=translator.token, content=translation, username=f'{event.message.member.display_name} ({language.name.lower()})', avatar_url=event.message.member.avatar_url if event.message.member.avatar_url else event.message.member.default_avatar_url)
            await event.app.rest.delete_webhook(webhook=translator)

@plugin.command
@lightbulb.app_command_permissions(perms=hikari.Permissions.MANAGE_CHANNELS, dm_enabled=False)
@lightbulb.add_cooldown(length=10.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.command('translator', 'Edit automatic text translation with the bot.')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def autotranslation(ctx: lightbulb.Context) -> None:
    return

@autotranslation.child
@lightbulb.command('info', 'Get information about the automatic text translation settings.')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def info(ctx: lightbulb.Context) -> None:
    webhooks = await ctx.bot.rest.fetch_guild_webhooks(ctx.guild_id)
    translators = get_translators(webhooks)
    embed = hikari.Embed(title='Translator Settings', color=get_setting('settings', 'embed_color'))
    embed.add_field(name='Confidence Threshold', value=f'- Default: 0.8\n- Current: {get_setting("settings", "auto_translate_conf")}', inline=True)
    embed.add_field(name='Minimum Relative Distance', value=f'- Default: 0.9\n- Current: {get_setting("settings", "auto_translate_min_relative_distance")}', inline=True)
    embed.add_field(name='Active Channels', value=', '.join([f'<#{translator.channel_id}>' for translator in translators]) if translators else 'No active channels.', inline=False)
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@autotranslation.child
@lightbulb.command('enable', 'Activate automated translation for this channel.')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def enable(ctx: lightbulb.Context) -> None:
    webhooks = await ctx.bot.rest.fetch_channel_webhooks(ctx.channel_id)
    translators = get_translators(webhooks)
    if len(translators) > 0:
        embed = hikari.Embed(description=f'Automated translation is currently active in <#{ctx.channel_id}> channel.', color=get_setting('settings', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    embed = hikari.Embed(description=f'Automated translation has been activated for <#{ctx.channel_id}> channel.', color=get_setting('settings', 'embed_color'))
    await ctx.bot.rest.create_webhook(channel=ctx.channel_id, name='Translator', avatar=ctx.app.get_me().display_avatar_url)
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@autotranslation.child
@lightbulb.command('disable', 'Deactivate automated translation for this channel.')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def disable(ctx: lightbulb.Context) -> None:
    webhooks = await ctx.bot.rest.fetch_channel_webhooks(ctx.channel_id)
    translators = get_translators(webhooks)
    if len(translators) > 0:
        translator = translators[0]
        embed = hikari.Embed(description=f'Automated translation has been successfully deactivated in <#{ctx.channel_id}> channel.', color=get_setting('settings', 'embed_color'))
        await ctx.bot.rest.delete_webhook(translator)
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    embed = hikari.Embed(description=f'Automated translation is currently inactive for the <#{ctx.channel_id}> channel.', color=get_setting('settings', 'embed_error_color'))
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)


@autotranslation.child
@lightbulb.option('value', '1.0 means absolute confidence; 0.0 means no confidence. (default: 0.80)', type=float, min_value=0.0, max_value=1.0, required=True)
@lightbulb.command('confidence', 'Set automatic text translation confidence value threshold.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def confidence(ctx: lightbulb.Context, value: float) -> None:
    if ctx.author.id not in ctx.bot.owner_ids:
        embed = hikari.Embed(description='You do not have permission to use this command!', color=get_setting('settings', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    
    try:
        write_setting('settings', 'auto_translate_conf', round(value, 2))
        embed = hikari.Embed(description=f'Automatic text translation confidence has been set to {round(value, 2)}.', color=get_setting('settings', 'embed_color'))
    except:
        embed = hikari.Embed(description=f'Failed to set automatic text confidence!', color=get_setting('settings', 'embed_error_color'))
    
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        
        
@autotranslation.child
@lightbulb.option('value', '0.99 means high distinction; 0.0 allows close probabilities for predictions (default: 0.90).', type=float, min_value=0.0, max_value=0.99, required=True)
@lightbulb.command('minimum-relative-distance', 'Set a distance for accurate language detection based on probability differences and text length.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def relative_distance(ctx: lightbulb.Context, value: bool) -> None:
    if ctx.author.id not in ctx.bot.owner_ids:
        embed = hikari.Embed(description='You do not have permission to use this command!', color=get_setting('settings', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    
    try:
        write_setting('settings', 'auto_translate_min_relative_distance', round(value, 2))
        embed = hikari.Embed(description=f'Automatic text translation minimum relative distance has been set to {round(value, 2)}.', color=get_setting('settings', 'embed_color'))
    except:
        embed = hikari.Embed(description=f'Failed to set automatic text translation minimum relative distance!', color=get_setting('settings', 'embed_error_color'))
    
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def get_lang(lang: str):
    with open('assets/json/language.json', 'r') as openfile:
        data = json.load(openfile)
        for item in data.items():
            if item[1] == lang:
                return item[0]
        return 'Language not found'

def get_translators(webhooks: Sequence[hikari.PartialWebhook]) -> Sequence[hikari.PartialWebhook]:
    translators = []
    for webhook in webhooks:
        if webhook.name == 'Translator':
            translators.append(webhook)
    return translators

def load(bot):
    bot.add_plugin(plugin)