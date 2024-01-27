import hikari
import lightbulb
import json

from bot import ADMIN_GUILD_ID, get_setting, write_setting
from deep_translator import GoogleTranslator
from lingua import Language, LanguageDetectorBuilder

plugin = lightbulb.Plugin('Translator')

# @plugin.listener(hikari.StartedEvent)
# async def available_languages(event: hikari.StartedEvent) -> None:
#     print(f'google: {GoogleTranslator().get_supported_languages()}\n')
#     print(f'lingua: {Language.all()}\n')

@plugin.listener(hikari.MessageCreateEvent)
async def print_translation(event: hikari.MessageCreateEvent) -> None:
    if get_setting('settings', 'auto_translate'):
        if event.is_bot or not event.content:
            return
        
        text = event.content
        detector = LanguageDetectorBuilder.from_all_languages().with_minimum_relative_distance(get_setting('settings', 'auto_translate_min_relative_distance')).build()
        language = detector.detect_language_of(text)
        confidence = detector.compute_language_confidence(text, language)
        
        # try:
        #     print(f'lang: {language.name} conf: {confidence}')
        # except:
        #     pass

        if language != Language.ENGLISH and confidence > get_setting('settings', 'auto_translate_conf') and get_lang(language.name) != 'Language not found':
            translation = GoogleTranslator(source=get_lang(language.name), target='en').translate(text)
            await event.message.respond(translation, reply=True)

@plugin.command
@lightbulb.app_command_permissions(perms=hikari.Permissions.MANAGE_CHANNELS, dm_enabled=False)
@lightbulb.add_cooldown(length=10.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.command('translate', 'Edit automatic text translation with the bot.')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def translate(ctx: lightbulb.Context) -> None:
    return

@translate.child
@lightbulb.option('value', 'Set auto translation to True or False', type=bool, required=True)
@lightbulb.command('set', 'Toggles automatic text translation.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def set(ctx: lightbulb.Context, value: bool) -> None:
    try:
        write_setting('settings', 'auto_translate', value)
        embed = hikari.Embed(description=f'Automatic text translation has been set to {value}.', color=get_setting('settings', 'embed_color'))
    except:
        embed = hikari.Embed(description=f'Failed to set automatic text translation!', color=get_setting('settings', 'embed_error_color'))
    
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@translate.child
@lightbulb.option('value', '1.0 means absolute confidence; 0.0 means no confidence. (default: 0.80)', type=float, min_value=0.0, max_value=1.0, required=True)
@lightbulb.command('confidence', 'Set automatic text translation confidence value threshold.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def set(ctx: lightbulb.Context, value: float) -> None:
    try:
        write_setting('settings', 'auto_translate_conf', round(value, 2))
        embed = hikari.Embed(description=f'Automatic text translation confidence has been set to {round(value, 2)}.', color=get_setting('settings', 'embed_color'))
    except:
        embed = hikari.Embed(description=f'Failed to set automatic text confidence!', color=get_setting('settings', 'embed_error_color'))
    
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

@translate.child
@lightbulb.option('value', '0.99 means high distinction; 0.0 allows close probabilities for predictions (default: 0.90).', type=float, min_value=0.0, max_value=0.99, required=True)
@lightbulb.command('minimum-relative-distance', 'Set a distance for accurate language detection based on probability differences and text length.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def set(ctx: lightbulb.Context, value: bool) -> None:
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

def load(bot):
    bot.add_plugin(plugin)