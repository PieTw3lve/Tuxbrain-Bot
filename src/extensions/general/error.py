import hikari
import lightbulb

from bot import get_setting

loader = lightbulb.Loader()

@loader.error_handler
async def handler(exc: lightbulb.exceptions.ExecutionPipelineFailedException) -> bool:
    embed = (hikari.Embed(description="I have errored, and I cannot get up", color=get_setting("general", "embed_error_color")))
    await exc.context.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    raise exc.invocation_failure

def format_seconds(seconds):
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