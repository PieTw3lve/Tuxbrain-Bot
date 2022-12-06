import hikari
import lightbulb

from googletrans import Translator

plugin = lightbulb.Plugin('Translator')

translator = Translator()
autoTL = False

@plugin.listener(hikari.MessageCreateEvent)
async def print_translation(event: hikari.MessageCreateEvent) -> None:
    global autoTL
    if autoTL:
        if event.is_bot or not event.content:
            return
        text = event.content
        lang = find_full_lang(translator.detect(text).lang)
        conf = translator.detect_legacy(text).confidence
        if lang != 'en':
            translation = translator.translate(text, dest='en')
            await event.message.respond(f'{lang} ({conf:.02f}): {translation.text}', reply=True)

@plugin.command
@lightbulb.add_cooldown(length=10.0, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.command('tl', 'Toggles automatic text translation.')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def toggle(ctx: lightbulb.Context) -> None:
    global autoTL
    if autoTL:
        embed = (hikari.Embed(description=f'Automatic text translation has been set to False.', color='#FF0000'))
    else:
        embed = (hikari.Embed(description=f'Automatic text translation has been set to True.', color='#32CD32'))
    autoTL = not autoTL
    await ctx.respond(embed)

def get_conf_indicator(confidence):
    if confidence > 0.8:
        return '🟩'
    elif confidence > 0.6:
        return '🟨'
    elif confidence > 0.4:
        return '🟧'
    else:
        return '🟥'

def find_full_lang(lang) -> str:
    match lang:
        case 'af':
            return 'Afrikaans'
        case 'ga':
            return 'Irish'
        case 'sq':
            return 'Albanian'
        case 'it':
            return 'Italian'
        case 'ar':
            return 'Arabic'
        case 'ja':
            return 'Japanese'
        case 'az':
            return 'Azerbaijani'
        case 'kn':
            return 'Kannada'
        case 'eu':
            return 'Basque'
        case 'ko':
            return 'Korean'
        case 'bn':
            return 'Bengali'
        case 'la':
            return 'Latin'
        case 'be':
            return 'Belarusian'
        case 'lv':
            return 'Latvian'
        case 'bg':
            return 'Bulgarian'
        case 'lt':
            return 'Lithuanian'
        case 'ca':
            return 'Catalan'
        case 'mk':
            return 'Macedonian'
        case 'zh-CN':
            return 'Chinese Simplified'
        case 'ms':
            return 'Malay'
        case 'zh-TW':
            return 'Chinese Traditional'
        case 'mt':
            return 'Maltese'
        case 'hr':
            return 'Croatian'
        case 'no':
            return 'Norwegian'
        case 'cs':
            return 'Czech'
        case 'fa':
            return 'Persian'
        case 'da':
            return 'Danish'
        case 'pl':
            return 'Polish'
        case 'nl':
            return 'Dutch'
        case 'pt':
            return 'Portuguese'
        case 'ro':
            return 'Romanian'
        case 'eo':
            return 'Esperanto'
        case 'ru':
            return 'Russian'
        case 'et':
            return 'Estonian'
        case 'sr':
            return 'Serbian'
        case 'tl':
            return 'Filipino'
        case 'sk':
            return 'Slovak'
        case 'fi':
            return 'Finnish'
        case 'sl':
            return 'Slovenian'
        case 'fr':
            return 'French'
        case 'es':
            return 'Spanish'
        case 'gl':
            return 'Galician'
        case 'sw':
            return 'Swahili'
        case 'ka':
            return 'Georgian'
        case 'sv':
            return 'Swedish'
        case 'de':
            return 'German'
        case 'ta':
            return 'Tamil'
        case 'el':
            return 'Greek'
        case 'te':
            return 'Telugu'
        case 'gu':
            return 'Gujarati'
        case 'th':
            return 'Thai'
        case 'ht':
            return 'Haitian Creole'
        case 'tr':
            return 'Turkish'
        case 'iw':
            return 'Hebrew'
        case 'uk':
            return 'Ukrainian'
        case 'hi':
            return 'Hindi'
        case 'ur':
            return 'Urdu'
        case 'hu':
            return 'Hungarian'
        case 'vi':
            return 'Vietnamese'
        case 'is':
            return 'Icelandic'
        case 'cy':
            return 'Welsh'
        case 'id':
            return 'Indonesian'
        case 'yi':
            return 'Yiddish'
    return 'en'

## Error Handler ##

@plugin.set_error_handler()
async def on_command_error(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event.exception, lightbulb.CommandNotFound):
        return
    if isinstance(event.exception, lightbulb.NotEnoughArguments):
        embed = (hikari.Embed(description='Not enough arguments were passed.\n' + ', '.join(event.exception.args), color='#FF0000'))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    if isinstance(event.exception, lightbulb.CommandIsOnCooldown):
        embed = (hikari.Embed(description=f'Command is on cooldown. Try again in {round(event.exception.retry_after)} second(s).', color='#FF0000'))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    if isinstance(event.exception, lightbulb.NotOwner):
        embed = (hikari.Embed(description=f'You do not have permission to use this command!', color='#FF0000'))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    embed = (hikari.Embed(description='I have errored, and I cannot get up', color='#FF0000'))
    await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    raise event.exception

## Add as a plugin ##

def load(bot):
    bot.add_plugin(plugin)