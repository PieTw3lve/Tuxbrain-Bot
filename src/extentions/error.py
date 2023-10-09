import hikari
import lightbulb

from bot import get_setting

plugin = lightbulb.Plugin('Error')

## Error Handler ##

class Error:
    @plugin.listener(lightbulb.CommandErrorEvent)
    async def on_command_error(event: lightbulb.CommandErrorEvent) -> None:
        if isinstance(event.exception, lightbulb.CommandNotFound):
            return
        if isinstance(event.exception, lightbulb.NotEnoughArguments):
            embed = (hikari.Embed(description='Not enough arguments were passed.\n' + ', '.join(event.exception.args), color=get_setting('settings', 'embed_error_color')))
            return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        if isinstance(event.exception, lightbulb.CommandIsOnCooldown):
            embed = (hikari.Embed(description=f'Command is on cooldown.\nTry again in {Error().format_seconds(round(event.exception.retry_after))}.', color=get_setting('settings', 'embed_error_color')))
            return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        if isinstance(event.exception, lightbulb.NotOwner):
            embed = (hikari.Embed(description=f'You do not have permission to use this command!', color=get_setting('settings', 'embed_error_color')))
            return await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        embed = (hikari.Embed(description='I have errored, and I cannot get up', color=get_setting('settings', 'embed_error_color')))
        await event.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        raise event.exception

    def format_seconds(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        time = []

        if days:
            time.append(f"{days} day{'s' if days > 1 else ''}")
            time.append(f"{hours} hour{'s' if hours > 1 else ''}")
        elif hours:
            time.append(f"{hours} hour{'s' if hours > 1 else ''}")
            time.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        elif minutes:
            time.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
            time.append(f"{seconds} second{'s' if seconds > 1 else ''}")
        else:
            time.append(f"{seconds} second{'s' if seconds > 1 else ''}")

        return " and ".join(time)

## Definitions ##

def load(bot):
    bot.add_plugin(plugin)