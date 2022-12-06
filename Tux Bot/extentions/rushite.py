import hikari
import lightbulb
import miru

plugin = lightbulb.Plugin('Rushite')

## Rushsite Subcommand ##

# @plugin.command
# @lightbulb.command('rushsite', 'Every command related to Rushsite.')
# @lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommandGroup)
# async def rushsite(ctx: lightbulb.Context) -> None:
#     pass
    
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