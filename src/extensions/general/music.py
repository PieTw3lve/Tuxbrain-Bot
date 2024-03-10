import hikari
import lightbulb
import lavalink
import re

from datetime import datetime
from bot import get_setting

plugin = lightbulb.Plugin('Music')

## Connect to Lavalink Server ##

@plugin.listener(hikari.ShardReadyEvent)
async def init(event: hikari.ShardReadyEvent) -> None:
    """Add node to bot on ready"""

    client = lavalink.Client(plugin.bot.get_me().id)
    client.add_node(
        host='localhost',
        port=2333,
        password='youshallnotpass',
        region='us',
        name='default-node'
    )

    client.add_event_hooks(EventHandler())
    plugin.bot.d.lavalink = client

@plugin.listener(hikari.VoiceServerUpdateEvent)
async def voice_server_update(event: hikari.VoiceServerUpdateEvent) -> None:
    # the data needs to be transformed before being handed down to
    # voice_update_handler
    lavalink_data = {
        't': 'VOICE_SERVER_UPDATE',
        'd': {
            'guild_id': event.guild_id,
            'endpoint': event.endpoint[6:],  # get rid of wss://
            'token': event.token,
        }
    }
    await plugin.bot.d.lavalink.voice_update_handler(lavalink_data)

@plugin.listener(hikari.VoiceStateUpdateEvent)
async def voice_state_update(event: hikari.VoiceStateUpdateEvent) -> None:
    # the data needs to be transformed before being handed down to
    # voice_update_handler
    lavalink_data = {
        't': 'VOICE_STATE_UPDATE',
        'd': {
            'guild_id': event.state.guild_id,
            'user_id': event.state.user_id,
            'channel_id': event.state.channel_id,
            'session_id': event.state.session_id,
        }
    }
    await plugin.bot.d.lavalink.voice_update_handler(lavalink_data)

## Song Subcommand ##

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('song', 'Enjoy and manage music playback.')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def song(ctx: lightbulb.Context) -> None:
    return

class PlayerManager():
    def __init__(self, player) -> None:
        self.player = player

    def milliseconds_to_youtube_timestamp(self, milliseconds: int) -> str:
        seconds, milliseconds = divmod(milliseconds, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
            
        if hours == 0 and minutes < 100:
            return f"{minutes:02d}:{seconds:02d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def queue_to_youtube_timestamp(self, queue: list) -> str:
        milliseconds = 0
        for track in queue:
            milliseconds += track.duration
        seconds, milliseconds = divmod(milliseconds, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_current_track_status(self):
        if self.player.paused:
            return ':pause_button:'
        else:
            return ':arrow_forward:'
    
    def move_marker(self, elapsed_time: int, total_time: int):
        line_length = 15
        marker = '🔘'
        empty_space = '▬'
        
        elapsed_milliseconds = elapsed_time / 1000  # Convert elapsed time to seconds
        total_milliseconds = total_time / 1000  # Convert total time to seconds

        if elapsed_milliseconds > total_milliseconds:
            elapsed_milliseconds = total_milliseconds

        progress = elapsed_milliseconds / total_milliseconds
        position_index = int(progress * line_length)

        # Create a string representing the line with the marker at the current position
        line = empty_space * position_index + marker + empty_space * (line_length - position_index)

        return line
    
    def truncate_string(self, song, max_length):
        return f"{song[:max_length - 3]}..." if len(song) > max_length else song

    def get_current_track(self):
        try:
            return f'[{self.player.current.title}]({self.player.current.uri})\nRequested by: <@{self.player.current.requester}>\n\n{self.get_current_track_status()} **{self.move_marker(int(self.player.position), self.player.current.duration)}** `[{self.milliseconds_to_youtube_timestamp(int(self.player.position))}/{self.milliseconds_to_youtube_timestamp(self.player.current.duration)}]` :sound:'
        except AttributeError:
            return 'Nothing, no more tacks are in queue.'


## Join Command ##

@song.child
@lightbulb.command('join', 'Joins the voice channel you are in.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def join(ctx: lightbulb.Context) -> None:
    """
        Connect the bot to the voice channel the user is currently in 
        and create a player_manager if it doesn't exist yet.
    """

    channel_id = await _join(ctx)
    if not channel_id:
        embed = hikari.Embed( description='Connect to a voice channel first!', color=(get_setting('settings', 'embed_error_color')))
        return await ctx.respond(embed)
    embed = hikari.Embed(title='Connected', description=f'Connected to <#{channel_id}>', color=(get_setting('settings', 'embed_color')), timestamp=datetime.now().astimezone())
    embed.set_footer(text=f'Requested by {ctx.author.username}', icon=ctx.author.display_avatar_url)
    await ctx.respond(embed)

    # print('Client connected to voice channel on guild: %s', ctx.guild_id)

## Leave Command ##

@song.child
@lightbulb.command('leave', 'Leaves voice channel, clearing queue.', auto_defer=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def leave(ctx: lightbulb.Context) -> None:
    """Leaves the voice channel the bot is in, clearing the queue."""

    playerManager = PlayerManager(plugin.bot.d.lavalink.player_manager.get(ctx.guild_id))
    clientVoiceState = ctx.bot.cache.get_voice_state(ctx.guild_id, ctx.author)
    
    if not playerManager.player or not playerManager.player.is_connected:
        embed = hikari.Embed(description='Not currently in any voice channel!', color=(get_setting('settings', 'embed_error_color')))
        return await ctx.respond(embed)
    elif clientVoiceState.channel_id != playerManager.player.channel_id:
        embed = hikari.Embed(description='Not currently in same voice channel!', color=(get_setting('settings', 'embed_error_color')))
        return await ctx.respond(embed)

    await playerManager.player.set_pause(False) # turn off pause
    playerManager.player.set_shuffle(False) # turn off shuffle
    playerManager.player.set_loop(0)  # turn off loop
    playerManager.player.queue.clear()  # clear queue
    await playerManager.player.stop()  # stop player
    playerManager.player.channel_id = None  # update the channel_id of the player to None
   
    await plugin.bot.update_voice_state(ctx.guild_id, None)
   
    embed = hikari.Embed(title='Disconnected', description=f'Disconnected from <#{clientVoiceState.channel_id}>', color=(get_setting('settings', 'embed_color')), timestamp=datetime.now().astimezone())
    embed.set_footer(text=f'Requested by {ctx.author.username}', icon=ctx.author.display_avatar_url)
    await ctx.respond(embed)

## Play Command ##

@song.child
@lightbulb.option('query', 'Youtube URL, Twitch URL, SoundCloud URL, Bandcamp URL, Vimeo URL, or search query.', modifier=lightbulb.OptionModifier.CONSUME_REST, autocomplete=True, required=True)
@lightbulb.command('play', 'Searches query on youtube, or adds the URL to the queue.', auto_defer = True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def play(ctx: lightbulb.Context) -> None:
    """Searches the query on youtube, or adds the URL to the queue."""
    
    playerManager = PlayerManager(plugin.bot.d.lavalink.player_manager.get(ctx.guild_id))
    # Remove leading and trailing <>. <> may be used to suppress embedding links in Discord.
    query = ctx.options.query.strip('<>')
    
    if not playerManager.player or not playerManager.player.is_connected:
        channel_id = await _join(ctx)
        if not channel_id:
            embed = hikari.Embed(description='Connect to a voice channel first!', color=(get_setting('settings', 'embed_error_color')))
            return await ctx.respond(embed)
    
    # Get player again after having connected to voice channel
    playerManager = PlayerManager(plugin.bot.d.lavalink.player_manager.get(ctx.guild_id))

    # Get the results for the query from Lavalink.
    results = await playerManager.player.node.get_tracks(query)

    # Results could be None if Lavalink returns an invalid response (non-JSON/non-200 (OK)).
    # Alternatively, results.tracks could be an empty array if the query yielded no tracks.
    if not results or not results.tracks:
        embed = hikari.Embed(description='Nothing found!', color=get_setting('settings', 'embed_error_color'))
        return await ctx.respond(embed)

    embed = hikari.Embed(color=get_setting('settings', 'embed_success_color'), timestamp=datetime.now().astimezone())
    embed.set_footer(text=f'Requested by {ctx.author.username}', icon=ctx.author.display_avatar_url)

    if results.load_type == 'PLAYLIST_LOADED':
        tracks = results.tracks

        embed.title = 'Playlist Enqueued!'
        embed.description = f'{results.playlist_info.name} - {len(tracks)} tracks'
    
        for track in tracks:
                # Add all of the tracks from the playlist to the queue.
                playerManager.player.add(requester=ctx.author.id, track=track)
    else:
        track = results.tracks[0]
        embed.title = 'Track Enqueued'
        embed.description = f'[{track.title}]({track.uri})\n\n:stop_button: **🔘▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬** `[{playerManager.milliseconds_to_youtube_timestamp(track.duration)}]` :sound:'
        embed.set_thumbnail(f'https://img.youtube.com/vi/{track.identifier}/maxresdefault.jpg')
        playerManager.player.add(requester=ctx.author.id, track=track)

    await ctx.respond(embed)

    # We don't want to call .play() if the player is playing as that will effectively skip the current track.
    if not playerManager.player.is_playing:
        await playerManager.player.play()

@play.autocomplete("query")
async def search_autocomplete(opt: hikari.AutocompleteInteractionOption, inter: hikari.AutocompleteInteraction):
    resultList = []
    query = opt.value.strip('<>')

    # Check if the user input might be a URL. If it isn't, we can Lavalink do a YouTube search for it instead.
    url_rx = re.compile(r'https?://(?:www\.)?.+')
    if not url_rx.match(query):
        ytquery = f'ytsearch:{query}'
        scquery = f'scsearch:{query}'

    # Get the results for the query from Lavalink.
    if len(opt.value) > 0 and len(opt.value) <= 100:
        try:
            results = [await plugin.bot.d.lavalink.get_tracks(ytquery), await plugin.bot.d.lavalink.get_tracks(scquery)] 
        except UnboundLocalError:
            results = [await plugin.bot.d.lavalink.get_tracks(query)]
    else:
        return []

    # Gets a list of tracks or playlists.
    match results[0].load_type:
        case 'PLAYLIST':
            playlist = results[0].playlist_info
            name = f'{f"💿 {playlist.name}"[:100 - {3}]}... ({len(results[0].tracks)} Tracks)' if len(f'💿 {playlist.name} ({len(results[0].tracks)} Tracks)') > 100 else f'💿 {playlist.name} ({len(results[0].tracks)} Tracks)'
            value = opt.value
            option = hikari.impl.AutocompleteChoiceBuilder(name, value)
            resultList.append(option) 
        case 'TRACK':
            track = results[0].tracks[0]
            name = f'{f"🎶 {track.title}"[:100 - (3 + len(f" - {track.author}"))]}... - {track.author}' if len(f'🎶 {track.title} - {track.author}') > 100 else f'🎶 {track.title} - {track.author}'
            value = track.uri
            option = hikari.impl.AutocompleteChoiceBuilder(name, value)
            resultList.append(option)
        case 'SEARCH':
            for track in results[0].tracks[:5]:
                name = f'{f"YouTube: 🎶 {track.title}"[:100 - (3 + len(f" - {track.author}"))]}... - {track.author}' if len(f'Youtube: 🎶 {track.title} - {track.author}') > 100 else f'Youtube: 🎶 {track.title} - {track.author}'
                value = track.uri
                option = hikari.impl.AutocompleteChoiceBuilder(name, value)
                resultList.append(option)
            for track in results[1].tracks[:5]:
                name = f'{f"SoundCloud: 🎶 {track.title}"[:100 - (3 + len(f" - {track.author}"))]}... - {track.author}' if len(f'Soundcloud: 🎶 {track.title} - {track.author}') > 100 else f'Soundcloud: 🎶 {track.title} - {track.author}'
                value = track.uri
                if len(value) < 100:
                    option = hikari.impl.AutocompleteChoiceBuilder(name, value)
                    resultList.append(option)
        case _:
            return []
    
    return resultList

## Queue Command ##

@song.child
@lightbulb.command('queue', 'Get a list of the queue.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def queue(ctx: lightbulb.Context) -> None:
    playerManager = PlayerManager(plugin.bot.d.lavalink.player_manager.get(ctx.guild_id))
    if not playerManager.player.is_playing:
        embed = hikari.Embed(description='No track is playing!', color=(get_setting('settings', 'embed_error_color')))
        return await ctx.respond(embed)
    
    queue = []
    pages = (len(playerManager.player.queue) + 9) // 10
    
    for index, item in enumerate(playerManager.player.queue[:10], start=1):
        queue.append(f"`{index}.` [{playerManager.truncate_string(item.title, 50)}]({item.uri}) `[{playerManager.milliseconds_to_youtube_timestamp(item.duration)}]`")
    
    embed = hikari.Embed(title='Now Playing', description=f'{playerManager.get_current_track()}\n\n**Up next:**\n{f"{chr(10)}".join(queue)}' if len(queue) != 0 else f'{playerManager.get_current_track()}\n\n**Up next:**\n- No tracks in queue!', color=(get_setting('settings', 'embed_color')), timestamp=datetime.now().astimezone())
    embed.set_thumbnail(f'https://img.youtube.com/vi/{playerManager.player.current.identifier}/maxresdefault.jpg')
    embed.add_field(name='In queue', value=len(playerManager.player.queue), inline=True)
    embed.add_field(name='Total length', value=playerManager.queue_to_youtube_timestamp(playerManager.player.queue), inline=True)
    embed.add_field(name='Page', value=f'1 out of {pages}' if pages != 0 else '1 out of 1', inline=True)
    embed.set_footer(text=f'Requested by {ctx.author.username}', icon=ctx.author.display_avatar_url)
    
    await ctx.respond(embed)

## Controller Command ##

@song.child
@lightbulb.option('option', 'List of modifiers', choices=['Pause', 'Skip', 'Shuffle', 'Loop', 'Clear'], required=True)
@lightbulb.command('controller', 'Manage music player options.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def controller(ctx: lightbulb.Context, option: str) -> None:
    playerManager = PlayerManager(plugin.bot.d.lavalink.player_manager.get(ctx.guild_id))
    clientVoiceState = ctx.bot.cache.get_voice_state(ctx.guild_id, ctx.author)
    if not playerManager.player or not playerManager.player.is_connected:
        embed = hikari.Embed(description='Not currently in any voice channel!', color=(get_setting('settings', 'embed_error_color')))
        return await ctx.respond(embed)
    elif not playerManager.player.is_playing:
        embed = hikari.Embed(description='No track is playing!', color=(get_setting('settings', 'embed_error_color')))
        return await ctx.respond(embed)
    elif clientVoiceState.channel_id != playerManager.player.channel_id:
        embed = hikari.Embed(description='Not currently in same voice channel!', color=(get_setting('settings', 'embed_error_color')))
        return await ctx.respond(embed)
    
    match option:
        case 'Pause':
            paused = not playerManager.player.paused
            await playerManager.player.set_pause(paused)
            embed = hikari.Embed(title='Track Paused' if paused else 'Track Unpaused', description=playerManager.get_current_track(), color=(get_setting('settings', 'embed_important_color')), timestamp=datetime.now().astimezone())
            embed.set_thumbnail(f'https://img.youtube.com/vi/{playerManager.player.current.identifier}/maxresdefault.jpg')
            embed.set_footer(text=f'Requested by {ctx.author.username}', icon=ctx.author.display_avatar_url)
            await ctx.respond(embed)
        case 'Skip':
            await playerManager.player.skip()
            embed = hikari.Embed(title='Track Skipped: Now Playing', description=playerManager.get_current_track(), color=(get_setting('settings', 'embed_important_color')), timestamp=datetime.now().astimezone())
            try:
                embed.set_thumbnail(f'https://img.youtube.com/vi/{playerManager.player.current.identifier}/maxresdefault.jpg')
            except AttributeError:
                pass
            embed.set_footer(text=f'Requested by {ctx.author.username}', icon=ctx.author.display_avatar_url)
            await ctx.respond(embed)
        case 'Shuffle':
            shuffle = not playerManager.player.shuffle
            playerManager.player.set_shuffle(shuffle)
            embed = hikari.Embed(title='Track Shuffled' if shuffle else 'Track Unshuffled', description='Shuffling entire queue...' if shuffle else 'Unshuffling entire queue...', color=(get_setting('settings', 'embed_important_color')), timestamp=datetime.now().astimezone())
            embed.set_footer(text=f'Requested by {ctx.author.username}', icon=ctx.author.display_avatar_url)
            await ctx.respond(embed)
        case 'Loop':
            loop = (playerManager.player.loop + 1) % 3
            playerManager.player.set_loop(loop)
            if loop == 0:
                embed = hikari.Embed(title='Looping Off', description='Setting looping to off...', color=(get_setting('settings', 'embed_important_color')), timestamp=datetime.now().astimezone())
            elif loop == 1:
                embed = hikari.Embed(title='Looping Track', description='Currently looping single (current) track...', color=(get_setting('settings', 'embed_important_color')), timestamp=datetime.now().astimezone())
            elif loop == 2:
                embed = hikari.Embed(title='Looping Queue', description='Currently looping entire queue...', color=(get_setting('settings', 'embed_important_color')), timestamp=datetime.now().astimezone())
            embed.set_footer(text=f'Requested by {ctx.author.username}', icon=ctx.author.display_avatar_url)
            await ctx.respond(embed)
        case 'Clear':
            playerManager.player.queue.clear()
            embed = hikari.Embed(title='Queue Cleared', description='Clearing entire queue...', color=(get_setting('settings', 'embed_important_color')), timestamp=datetime.now().astimezone())
            embed.set_footer(text=f'Requested by {ctx.author.username}', icon=ctx.author.display_avatar_url)
            await ctx.respond(embed)

## Join Handler ##

async def _join(ctx: lightbulb.Context):
    states = plugin.bot.cache.get_voice_states_view_for_guild(ctx.guild_id)
    voice_state = [state[1] for state in filter(lambda i : i[0] == ctx.author.id, states.items())]

    # user not in voice channel
    if not voice_state:
        return
    
    channel_id = voice_state[0].channel_id  # channel user is connected to
    plugin.bot.d.lavalink.player_manager.create(guild_id=ctx.guild_id)
    
    await plugin.bot.update_voice_state(ctx.guild_id, channel_id, self_deaf=True)
    
    return channel_id

## Stop Queue Event ##

@plugin.listener(hikari.VoiceStateUpdateEvent) # Bot will leave VC if there is no one present
async def quit(event: hikari.VoiceStateUpdateEvent):
    if plugin.bot.cache.get_voice_state(event.guild_id, plugin.bot.get_me()): 
        voiceState = plugin.bot.cache.get_voice_states_view_for_channel(event.state.guild_id, event.state.channel_id) if event.state.channel_id else plugin.bot.cache.get_voice_states_view_for_channel(event.state.guild_id, event.old_state.channel_id)
        members = [vs.member for vs in voiceState.values()]
        
        if len(members) > 1:
            return
        
        await plugin.bot.update_voice_state(event.guild_id, None)

@plugin.listener(hikari.VoiceStateUpdateEvent) # Reset queue when Bot leaves VC
async def quit2(event: hikari.VoiceStateUpdateEvent): 
    if event.state.member.id == plugin.bot.get_me().id and event.old_state == event.state:
        playerManager = PlayerManager(plugin.bot.d.lavalink.player_manager.get(event.guild_id))
        await playerManager.player.set_pause(False) 
        playerManager.player.set_shuffle(False) 
        playerManager.player.set_loop(0)  
        playerManager.player.queue.clear()
        await playerManager.player.stop() 
        playerManager.player.channel_id = None
    
## Event Handler ##

class EventHandler:
    """Events from the Lavalink server"""
    @lavalink.listener(lavalink.TrackStartEvent)
    async def track_start(self, event: lavalink.TrackStartEvent):
        await event.player.set_volume(10)

    @lavalink.listener(lavalink.QueueEndEvent)
    async def queue_finish(self, event: lavalink.QueueEndEvent):
        await event.player.set_pause(False)
        event.player.set_shuffle(False) 
        event.player.set_loop(0) 
        await event.player.stop()
        event.player.channel_id = None
        await plugin.bot.update_voice_state(event.player.guild_id, None)
        
        # print('Queue finished on guild: %s', event.player.guild_id)

## Definitions ##

def load(bot):
    bot.add_plugin(plugin)