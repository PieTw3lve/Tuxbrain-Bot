import hikari
import lightbulb
import random

from bot import get_setting

plugin = lightbulb.Plugin('Coinflip')

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('number', 'Number of coinflip(s)', type=int, min_value=1, max_value=100, required=True)
@lightbulb.command('coinflip', 'Flip a coin.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def coinflip(ctx: lightbulb.SlashContext, number: int) -> None:
    result = []
    heads = 0
    tails = 0

    for i in range(number):
        number = random.randint(1,2)
        if number == 1:
            result.append('<:heads:1265769437814853733>')
            heads += 1
        else:
            result.append('<:tails:1265769509235593380>')
            tails += 1

    result = (' '.join(result))

    embed = (hikari.Embed(title='Coinflip Result:' if number == 1 else 'Coinflip Results:', description=result, color=get_setting('general', 'embed_color')))
    embed.add_field('Summary:', f'Heads: {heads} Tails: {tails}')
    await ctx.respond(embed)

def load(bot):
    bot.add_plugin(plugin)