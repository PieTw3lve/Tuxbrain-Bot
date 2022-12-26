import hikari
import lightbulb
import miru
import startup 

from datetime import datetime
from bot import get_setting

plugin = lightbulb.Plugin('Rushite')

# Rushsite Subcommand ##

@plugin.command
@lightbulb.command('rushsite', 'Every command related to Rushsite.')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommandGroup)
async def rushsite(ctx: lightbulb.Context) -> None:
    pass

## Rushsite SignUp ##

@rushsite.child
@lightbulb.option('logo', 'A logo that will represent your team.', type=hikari.Attachment, required=True)
@lightbulb.command('signup', 'Sign up for the current season of Rushsite!', pass_options=True)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashSubCommand)
async def signup(ctx: lightbulb.Context, logo: hikari.Attachment) -> None:
    if get_setting('rushsite_signup_accessible'):
        modal = SignupModal(logo)
        await modal.send(interaction=ctx.interaction)
    else:
        embed = hikari.Embed(description=f'Signup forms are currently not available!', color=get_setting('embed_error_color'))
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

class SignupModal(miru.Modal):
    name = miru.TextInput(label='Team Name', placeholder='Mr. Cool Guys', custom_id='team_name', style=hikari.TextInputStyle.SHORT, required=True)
    members = miru.TextInput(label='IGNs, origins, and roles of team members.', placeholder='s1mple (Ukraine, player), ryqn (France, player), KennyS (France, coach).', custom_id='members', style=hikari.TextInputStyle.PARAGRAPH, required=True)
    rank = miru.TextInput(label='Highest 5v5 ranked player in the team.', placeholder='Silver, Gold, Master Guardian, or Legendary Eagle.', custom_id='rank', style=hikari.TextInputStyle.SHORT, required=True)
    discord = miru.TextInput(label='Discord IGN of at least one team member.', placeholder='Pie12#1069', custom_id='discord', style=hikari.TextInputStyle.SHORT, required=True)
    
    def __init__(self, image: hikari.Attachment) -> None:
        super().__init__(title='Rushsite Signup Sheet', custom_id='signup', timeout=None)
        self.image = image
    
    async def callback(self, ctx: miru.ModalContext) -> None:
        embed = hikari.Embed(title=f'{self.name.value} signed up!', timestamp=datetime.now().astimezone(), color=get_setting('embed_color'))
        embed.set_thumbnail(self.image)
        embed.add_field(name='Team Name', value=self.name.value)
        embed.add_field(name='Members', value=self.members.value)
        embed.add_field(name='Highest Rank', value=self.rank.value)
        embed.add_field(name='Discord IGN', value=self.discord.value)
        
        await ctx.bot.rest.create_message(channel=get_setting('rushsite_signup_channel'), embed=embed)
        
        embed = hikari.Embed(description=f'Success! You signed up!', color=get_setting('embed_success_color'))

        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

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

def set_stage_image(map):
    match map:
        case 'Vertigo':
            return r'''maps\vertigo.png'''
        case 'Cobblestone':
            return r'''maps\cobblestone.png'''
        case 'Train':
            return r'''maps\train.png'''
        case 'Shortdust':
            return r'''maps\shortdust.png'''
        case 'Blagai':
            return r'''maps\blagai.png'''
        case 'Overpass':
            return r'''maps\overpass.png'''
        case 'Nuke': 
            return r'''maps\nuke.png'''