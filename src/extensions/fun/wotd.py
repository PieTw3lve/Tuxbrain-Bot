import hikari
import lightbulb
import requests

from bot import get_setting

WORDNIK_API_KEY = get_setting('bot', 'wordnik_api_key')

plugin = lightbulb.Plugin('WOTD')

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('wotd', 'Retrieve the Word of the Day.')
@lightbulb.implements(lightbulb.SlashCommand)
async def today_word(ctx: lightbulb.Context) -> None:
    wordOfTheDayUrl = f"http://api.wordnik.com/v4/words.json/wordOfTheDay?api_key={WORDNIK_API_KEY}"
    response = requests.get(wordOfTheDayUrl)
    if response.status_code == 200:
        embed = hikari.Embed(color=get_setting('settings', 'embed_color'))
        word = response.json()
        wordText = word['word'].capitalize()
        note = word['note']
        definitions = word['definitions']
        examples = word['examples']
        embed.title = f'Word of the day: {wordText}'
        embed.description = f'{note}\n\n**Definitions:**'
        for definition in definitions:
            embed.description = f'{embed.description}\n{definition["partOfSpeech"].capitalize()}: {definition["text"]}'
        embed.description = f'{embed.description}\n\n**Examples:**'
        for example in examples:
            embed.description = f'{embed.description}\n- {example["text"]}'
    else:
        embed = hikari.Embed(title='Failed to get the word of the day', description='Did you fill in your Wordnik api key?', color=get_setting('settings', 'embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    await ctx.respond(embed)

def load(bot):
    bot.add_plugin(plugin)