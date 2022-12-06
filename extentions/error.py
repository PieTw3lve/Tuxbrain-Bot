import hikari
import lightbulb

plugin = lightbulb.Plugin('error')

## Error Handler ##

class ErrorHandler(lightbulb.CommandErrorEvent):
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
    # bot.add_plugin(ErrorHandler())