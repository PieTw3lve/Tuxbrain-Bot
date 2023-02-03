import openai
import hikari
import lightbulb

from startup import OPENAI_API_KEY
from bot import get_setting

plugin = lightbulb.Plugin('OpenAI')
openai.api_key = OPENAI_API_KEY


## OpenAI Text Command ##

@plugin.command
@lightbulb.option('prompt', 'Enter a question, conversation, or tl:dr.', type=str, required=True)
@lightbulb.command('ask', 'Uses OpenAI to respond to a prompt.', pass_options=True, auto_defer=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def ask(ctx: lightbulb.Context, prompt: str) -> None:
    try:
        completion = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=256,
            temperature=0.5,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        reply = completion.choices[0].text
        embed = hikari.Embed(title=prompt, description=reply, color=get_setting('embed_color'))
        
        await ctx.respond(embed)
    except:
        embed = hikari.Embed(description="Prompt was invalid!", color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return

## OpenAI Image Command ##

# @plugin.command
# @lightbulb.option('prompt', 'Enter a description.', type=str, required=True)
# @lightbulb.command('ask-image', 'Uses OpenAI to create an image based on the prompt.', pass_options=True, auto_defer=True)
# @lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
# async def ask_image(ctx: lightbulb.Context, prompt: str) -> None:
#     try:
#         response = openai.Image.create(
#             prompt=prompt,
#             n=1,
#             size="1024x1024"
#         )
        
#         image_url = response['data'][0]['url']
#         await ctx.respond(embed)
    
#         embed = hikari.Embed(title=prompt, description=image_url, color=get_setting('embed_color'))
#     except:
#         embed = hikari.Embed(description="Prompt was invalid!", color=get_setting('embed_error_color'))
#         await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
#         return

## Error Handler ##

@plugin.set_error_handler()
async def on_command_error(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event.exception, lightbulb.CommandNotFound):
        return
    if isinstance(event.exception, lightbulb.NotEnoughArguments):
        embed = (hikari.Embed(description='Not enough arguments were passed.\n' + ', '.join(event.exception.args), color=get_setting('embed_error_color')))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    if isinstance(event.exception, lightbulb.CommandIsOnCooldown):
        embed = (hikari.Embed(description=f'Command is on cooldown. Try again in {round(event.exception.retry_after)} second(s).', color=get_setting('embed_error_color')))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    if isinstance(event.exception, lightbulb.NotOwner):
        embed = (hikari.Embed(description=f'You do not have permission to use this command!', color=get_setting('embed_error_color')))
        return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    embed = (hikari.Embed(description='I have errored, and I cannot get up', color=get_setting('embed_error_color')))
    await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    raise event.exception

## Definitions ##

def load(bot):
    bot.add_plugin(plugin)