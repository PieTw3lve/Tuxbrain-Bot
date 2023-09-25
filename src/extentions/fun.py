import hikari
import lightbulb
import miru
import requests
import json
import re

from bot import WORDNIK_API_KEY, get_setting

plugin = lightbulb.Plugin('Fun')

## Random Animals ##

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('random', 'Get something random!')
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def rand(ctx: lightbulb.Context) -> None:
    pass

@rand.child
@lightbulb.command('fox', 'Get a random picture of a fox!')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def today_fact(ctx: lightbulb.Context) -> None:
    url = 'https://apilist.fun/out/randomfox'
    request = dict(json.loads(requests.get(url).text))
    
    await ctx.respond(request.get('image'))

@rand.child
@lightbulb.command('cat', 'Get a random picture of a cat!')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def today_fact(ctx: lightbulb.Context) -> None:
    url = 'https://api.thecatapi.com/v1/images/search'
    request = list(json.loads(requests.get(url).text))
    
    await ctx.respond(request[0].get('url'))

@rand.child
@lightbulb.command('dog', 'Get a random picture of a dog!')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def today_fact(ctx: lightbulb.Context) -> None:
    url = 'https://apilist.fun/out/randomdog'
    request = dict(json.loads(requests.get(url).text))
    
    await ctx.respond(request.get('url'))

## Random Joke Command ##

@rand.child
@lightbulb.command('joke', 'Get a random unfunny joke!')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def joke(ctx: lightbulb.Context) -> None:
    url = 'https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit&type=twopart'
    request = dict(json.loads(requests.get(url).text))
    
    embed = hikari.Embed(title=request.get('setup'), description=f"||{request.get('delivery')}||", color=get_setting('settings', 'embed_color'))
    await ctx.respond(embed)

## Random Riddle Command ##

@rand.child
@lightbulb.command('riddle', 'Get a random riddle!')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def riddle(ctx: lightbulb.Context) -> None:
    url = 'https://riddles-api.vercel.app/random'
    request = dict(json.loads(requests.get(url).text))
    
    embed = hikari.Embed(title=request.get('riddle'), description=f"||{request.get('answer')}||", color=get_setting('settings', 'embed_color'))
    await ctx.respond(embed)

## Random Useless Fact Command ##

@rand.child
@lightbulb.command('fact', 'Get a random useless fact.')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def rand_fact(ctx: lightbulb.Context) -> None:
    url = 'https://uselessfacts.jsph.pl/random.json?language=en'
    request = dict(json.loads(requests.get(url).text))
    
    embed = hikari.Embed(title='Random Useless Fact', description=request.get('text'), color=get_setting('settings', 'embed_color'))
    await ctx.respond(embed)

## Useless Fact of the Day Command ##

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('fact', 'Get the useless fact of the day.')
@lightbulb.implements(lightbulb.SlashCommand)
async def today_fact(ctx: lightbulb.Context) -> None:
    url = 'https://uselessfacts.jsph.pl/today.json?language=en'
    request = dict(json.loads(requests.get(url).text))
    
    embed = hikari.Embed(title='Useless Fact of the Day!', description=request.get('text'), color=get_setting('settings', 'embed_color'))
    await ctx.respond(embed)

## Word of the Day Command ##

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('wotd', 'Get the word of the day.')
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

## Bored Command ##

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command('bored', 'Get an activity suggestion from the bot.')
@lightbulb.implements(lightbulb.SlashCommand)
async def bored(ctx: lightbulb.Context) -> None:
    url = 'https://www.boredapi.com/api/activity'
    request = dict(json.loads(requests.get(url).text))
    
    embed = hikari.Embed(title=f"{request.get('activity')}.", description=f"Type: {request.get('type').capitalize()}\nParticipants: {request.get('participants')}\n Price: 🪙 {request.get('price'):,}\nAccessibility: {request.get('accessibility')}", color=get_setting('settings', 'embed_color'))
    await ctx.respond(embed)

## Hangman Command ##

def contains_special_characters(input_string):
    pattern = r'[!@#$%^&*(),.?":{}|<>]'
    return bool(re.search(pattern, input_string))

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option('theme', 'The theme of the word!', type=str, required=True)
@lightbulb.option('word', 'The word players will have to guess!', type=str, required=True)
@lightbulb.command('hangman', 'Play a game of Hangman.', pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def hangman(ctx: lightbulb.Context, word: str, theme: str) -> None:
    if contains_special_characters(word):
        embed = hikari.Embed(description='You are not allowed to include special characters!', color=get_setting('settings', 'embed_error_color'))
        return await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

    embed = hikari.Embed(title=f'Hangman game has started!', description='This menu is only for hiding your command.', color=get_setting('settings', 'embed_color'))
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
    
    word = word.lower()
    guessers = {}

    embed = hikari.Embed(title=f'{ctx.user} has started a Hangman game!', description='`A perfect game to hang your mans!`', color=get_setting('settings', 'embed_color'))
    embed.set_image('assets/img/fun/hangman/0.png')
    embed.add_field(name='__Game info__', value=f'Host: <@{ctx.user.id}>\nWord Count: `{len(word.replace(" ", "")):,}`\nTheme: **{theme.capitalize()}**', inline=True)
    embed.add_field(name='__Guessers__', value=f'None', inline=True)
    embed.set_footer(text=f'The game will timeout in 2 minutes!')

    view = HangmanLobbyView(ctx.author, guessers, word, theme)
    
    message = await ctx.respond(embed, components=view.build(), reply=False)
    message = await message
    
    await view.start(message) # starts up lobby
    await view.wait() # waiting until lobby starts or timed out
    
    if not view.gameStart: # if lobby timed out
        return
    
    wordVisual = []
    charIndex = {}
    
    for char in word:
        if char != ' ':
            charIndex.update({char: []})
    for i in range(len(word)):
        if word[i] != ' ':
            charIndex[word[i]].append(i)
            wordVisual.append(r'''\_''')
        else:
            wordVisual.append('-')
    
    guessersIter = iter(view.game['guessers'].items())
    firstGuesser = next(guessersIter)[1]
    
    embed = hikari.Embed(title=f"It's {firstGuesser['name']} Turn!", description=f'Host: <@{ctx.user.id}>\nGuessers: {", ".join(view.game["guessers"])}\nWord Count: {len(view.game["word"].replace(" ", "")):,}\nTheme: **{view.game["theme"].capitalize()}**', color=get_setting('settings', 'embed_color'))
    embed.add_field(name='__Current letters__', value=' '.join(wordVisual), inline=True)
    embed.add_field(name='__Guesses__', value='None', inline=True)
    embed.set_image('assets/img/fun/hangman/0.png')
    embed.set_thumbnail(firstGuesser['url'])
        
    view = HangmanGameView(ctx.author.id, view.game, wordVisual, charIndex)
        
    message = await ctx.edit_last_response(embed, components=view.build())

    await view.start(message) # starts game

class HangmanLobbyView(miru.View):
    def __init__(self, author: hikari.User, guessers: dict, word: int, theme: int) -> None:
        super().__init__(timeout=120.0)
        self.game = {'author': author, 'guessers': guessers, 'word': word, 'theme': theme}
        self.gameStart = False
    
    @miru.button(label='Start', style=hikari.ButtonStyle.SUCCESS, row=1)
    async def start_game(self, button: miru.Button, ctx: miru.Context) -> None:
        if self.game['author'].id != ctx.user.id: # checks if user is host
            embed = hikari.Embed(description='You are not the host!', color=get_setting('settings', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        elif len(self.game['guessers']) == 0:
            embed = hikari.Embed(description='You do not have enough players!', color=get_setting('settings', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        self.gameStart = True
        self.stop()
    
    @miru.button(label='Join Game', style=hikari.ButtonStyle.PRIMARY, row=1)
    async def join(self, button: miru.Button, ctx: miru.Context) -> None:
        player = f'<@{ctx.user.id}>'
        playerInfo = {'name': f'{ctx.user.global_name}', 'id': ctx.user.id, 'url': ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url}
        
        if player in self.game['guessers'] or ctx.user.id == self.game["author"].id: # checks if user already joined
            embed = hikari.Embed(description='You already joined this game!', color=get_setting('settings', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        self.game['guessers'][player] = playerInfo
        
        embed = hikari.Embed(title=f'{self.game["author"]} has started a Hangman game!', description='`A perfect game to hang your mans!`', color=get_setting('settings', 'embed_color'))
        embed.add_field(name='__Game info__', value=f'Host: <@{self.game["author"].id}>\nWord Count: `{len(self.game["word"].replace(" ", "")):,}`\nTheme: **{self.game["theme"].capitalize()}**', inline=True)
        embed.add_field(name='__Guessers__', value=f'{", ".join(self.game["guessers"])}', inline=True)
        embed.set_image('assets/img/fun/hangman/0.png')
        embed.set_footer(text=f'The game will timeout in 2 minutes!')
        
        await ctx.message.edit(embed)
    
    async def on_timeout(self) -> None:      
        embed = hikari.Embed(title=f'Game has timed out!', color=get_setting('settings', 'embed_color'))
        embed.add_field(name='__Game info__', value=f'Host: <@{self.game["author"].id}>\nWord Count: `{len(self.game["word"].replace(" ", "")):,}`\nTheme: **{self.game["theme"].capitalize()}**', inline=True)
        embed.add_field(name='__Guessers__', value=f'{", ".join(self.game["guessers"])}' if len(self.game['guessers']) > 0 else 'None', inline=True)
        embed.set_image('assets/img/fun/hangman/0.png')
        embed.set_footer(text=f'The game will timeout in 2 minutes!')
        
        await self.message.edit(embed, components=[])
        self.stop()

class HangmanGameView(miru.View):
    def __init__(self, author: str, game: dict, wordVisual: list, charIndex: dict) -> None:
        super().__init__(timeout=None)
        self.author = author
        self.game = game
        self.wordVisual = wordVisual
        self.charIndex = charIndex
        
        self.guesses = []
        self.mistakes = 0
        
        self.guesserIter = iter(game['guessers'].items())
        self.guesser = next(self.guesserIter)[1]
        
    @miru.text_select(
        custom_id='alphabet_select_1',
        placeholder='Letters from A-M',
        options=[
            miru.SelectOption(label='🇦', description='Apple', value='a'),
            miru.SelectOption(label='🇧', description='Ball', value='b'),
            miru.SelectOption(label='🇨', description='Car', value='c'),
            miru.SelectOption(label='🇩', description='Doll', value='d'),
            miru.SelectOption(label='🇪', description='Eric', value='e'),
            miru.SelectOption(label='🇫', description='Fish', value='f'),
            miru.SelectOption(label='🇬', description='Goat', value='g'),
            miru.SelectOption(label='🇭', description='Hen', value='h'),
            miru.SelectOption(label='🇮', description='Ice Cream', value='i'),
            miru.SelectOption(label='🇯', description='Jug', value='j'),
            miru.SelectOption(label='🇰', description='Kite', value='k'),
            miru.SelectOption(label='🇱', description='Lion', value='l'),
            miru.SelectOption(label='🇲', description='Mango', value='m'),
        ],
        row=1
    )
    async def select_leter_1(self, select: miru.TextSelect, ctx: miru.Context):
        letter = select.values[0]
        
        if letter in self.guesses: # if player guessed that letter already
            embed = hikari.Embed(description='This letter has already been guessed!', color=get_setting('settings', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        try: # cycle turns
            self.guesser = next(self.guesserIter)[1]
        except:
            self.guesserIter = iter(self.game['guessers'].items())
            self.guesser = next(self.guesserIter)[1]
        
        if letter not in self.charIndex:
            self.mistakes = self.mistakes + 1
            self.guesses.append(letter)
            
            embed = hikari.Embed(title=f"Incorrect! It's {self.guesser['name']} Turn!", description=f'`{ctx.user.global_name} has guessed letter {letter.capitalize()}.`\n\nHost: <@{self.author}>\nGuessers: {", ".join(self.game["guessers"])}\nWord Count: `{len(self.game["word"].replace(" ", "")):,}`\nTheme: **{self.game["theme"].capitalize()}**', color=get_setting('settings', 'embed_color'))
            embed.add_field(name='__Current letters__', value=' '.join(self.wordVisual), inline=True)
            embed.add_field(name='__Guesses__', value=', '.join(self.guesses).upper() if len(self.guesses) > 0 else 'None', inline=True)
            embed.set_image(f'assets/img/fun/hangman/{self.mistakes}.png')
            embed.set_thumbnail(self.guesser['url'])

            if self.mistakes != 7:
                await ctx.edit_response(embed, components=self.build())
            else:
                embed = hikari.Embed(title=f"Incorrect, the word was {self.game['word'].capitalize()}! {self.game['author']} wins!", description=f'`{ctx.user.global_name} has guessed letter {letter.capitalize()}.`\n\nHost: <@{self.author}>\nGuessers: {", ".join(self.game["guessers"])}\nWord Count: `{len(self.game["word"].replace(" ", "")):,}`\nTheme: **{self.game["theme"].capitalize()}**', color=get_setting('settings', 'embed_color'))
                embed.add_field(name='__Current letters__', value=' '.join(self.wordVisual), inline=True)
                embed.add_field(name='__Guesses__', value=', '.join(self.guesses).upper() if len(self.guesses) > 0 else 'None', inline=True)
                embed.set_image(f'assets/img/fun/hangman/{self.mistakes}.png')
                embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
                
                await ctx.edit_response(embed, components=[])
            
            return
        else:
            index = self.charIndex[letter]
        
            for i in index:
                self.wordVisual[i] = letter
        
            embed = hikari.Embed(title=f"Correct! It's {self.guesser['name']} Turn!", description=f'`{ctx.user.global_name} has guessed letter {letter.capitalize()}.`\n\nHost: <@{self.author}>\nGuessers: {", ".join(self.game["guessers"])}\nWord Count: `{len(self.game["word"].replace(" ", "")):,}`\nTheme: **{self.game["theme"].capitalize()}**', color=get_setting('settings', 'embed_color'))
            embed.add_field(name='__Current letters__', value=' '.join(self.wordVisual), inline=True)
            embed.add_field(name='__Guesses__', value=', '.join(self.guesses).upper() if len(self.guesses) > 0 else 'None', inline=True)
            embed.set_image(f'assets/img/fun/hangman/{self.mistakes}.png')
            embed.set_thumbnail(self.guesser['url'])
        
            if r'''\_''' not in self.wordVisual:
                embed = hikari.Embed(title=f"Correct! The guessing team wins!", description=f'`{ctx.user.global_name} has guessed letter {letter.capitalize()}.`\n\nHost: <@{self.author}>\nGuessers: {", ".join(self.game["guessers"])}\nWord Count: `{len(self.game["word"].replace(" ", "")):,}`\nTheme: **{self.game["theme"].capitalize()}**', color=get_setting('settings', 'embed_color'))
                embed.add_field(name='__Current letters__', value=' '.join(self.wordVisual), inline=True)
                embed.add_field(name='__Guesses__', value=', '.join(self.guesses).upper() if len(self.guesses) > 0 else 'None', inline=True)
                embed.set_image(f'assets/img/fun/hangman/{self.mistakes}.png')
                embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
                
                await ctx.edit_response(embed, components=[])
                self.stop()
            else:
                await ctx.edit_response(embed, components=self.build())
            
            return
    
    @miru.text_select(
        custom_id='alphabet_select_2',
        placeholder='Letters from N-Z',
        options=[
            miru.SelectOption(label='🇳', description='Nest', value='n'),
            miru.SelectOption(label='🇴', description='Orange', value='o'),
            miru.SelectOption(label='🇵', description='Parrot', value='p'),
            miru.SelectOption(label='🇶', description='Queen', value='q'),
            miru.SelectOption(label='🇷', description='Rose', value='r'),
            miru.SelectOption(label='🇸', description='Ship', value='s'),
            miru.SelectOption(label='🇹', description='Telephone', value='t'),
            miru.SelectOption(label='🇺', description='Umbrella', value='u'),
            miru.SelectOption(label='🇻', description='Van', value='v'),
            miru.SelectOption(label='🇼', description='Watch', value='w'),
            miru.SelectOption(label='🇽', description='Xylophone', value='x'),
            miru.SelectOption(label='🇾', description='Yak', value='y'),
            miru.SelectOption(label='🇿', description='Zebra', value='z'),
        ],
        row=2
    )
    async def select_leter_2(self, select: miru.TextSelect, ctx: miru.Context):
        letter = select.values[0]
        
        if letter in self.guesses: # if player guessed that letter already
            embed = hikari.Embed(description='This letter has already been guessed!', color=get_setting('settings', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        try: # cycle turns
            self.guesser = next(self.guesserIter)[1]
        except:
            self.guesserIter = iter(self.game['guessers'].items())
            self.guesser = next(self.guesserIter)[1]
        
        if letter not in self.charIndex:
            self.mistakes = self.mistakes + 1
            self.guesses.append(letter)
            
            embed = hikari.Embed(title=f"Incorrect! It's {self.guesser['name']} Turn!", description=f'`{ctx.user.global_name} has guessed letter {letter.capitalize()}.`\n\nHost: <@{self.author}>\nGuessers: {", ".join(self.game["guessers"])}\nWord Count: `{len(self.game["word"].replace(" ", "")):,}`\nTheme: **{self.game["theme"].capitalize()}**', color=get_setting('settings', 'embed_color'))
            embed.add_field(name='__Current letters__', value=' '.join(self.wordVisual), inline=True)
            embed.add_field(name='__Guesses__', value=', '.join(self.guesses).upper() if len(self.guesses) > 0 else 'None', inline=True)
            embed.set_image(f'assets/img/fun/hangman/{self.mistakes}.png')
            embed.set_thumbnail(self.guesser['url'])

            if self.mistakes != 7:
                await ctx.edit_response(embed, components=self.build())
            else:
                embed = hikari.Embed(title=f"Incorrect, the word was {self.game['word'].capitalize()}! {self.game['author']} wins!", description=f'`{ctx.user.global_name} has guessed letter {letter.capitalize()}.`\n\nHost: <@{self.author}>\nGuessers: {", ".join(self.game["guessers"])}\nWord Count: {len(self.game["word"].replace(" ", "")):,}\nTheme: **{self.game["theme"].capitalize()}**', color=get_setting('settings', 'embed_color'))
                embed.add_field(name='__Current letters__', value=' '.join(self.wordVisual), inline=True)
                embed.add_field(name='__Guesses__', value=', '.join(self.guesses).upper() if len(self.guesses) > 0 else 'None', inline=True)
                embed.set_image(f'assets/img/fun/hangman/{self.mistakes}.png')
                embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
                
                await ctx.edit_response(embed, components=[])
            
            return
        else:
            index = self.charIndex[letter]
        
            for i in index:
                self.wordVisual[i] = letter
        
            embed = hikari.Embed(title=f"Correct! It's {self.guesser['name']} Turn!", description=f'`{ctx.user.global_name} has guessed letter {letter.capitalize()}.`\n\nHost: <@{self.author}>\nGuessers: {", ".join(self.game["guessers"])}\nWord Count: `{len(self.game["word"].replace(" ", "")):,}`\nTheme: **{self.game["theme"].capitalize()}**', color=get_setting('settings', 'embed_color'))
            embed.add_field(name='__Current letters__', value=' '.join(self.wordVisual), inline=True)
            embed.add_field(name='__Guesses__', value=', '.join(self.guesses).upper() if len(self.guesses) > 0 else 'None', inline=True)
            embed.set_image(f'assets/img/fun/hangman/{self.mistakes}.png')
            embed.set_thumbnail(self.guesser['url'])
        
            if r'''\_''' not in self.wordVisual:
                embed = hikari.Embed(title=f"Correct! The guessing team wins!", description=f'`{ctx.user.global_name} has guessed letter {letter.capitalize()}.`\n\nHost: <@{self.author}>\nGuessers: {", ".join(self.game["guessers"])}\nWord Count: `{len(self.game["word"].replace(" ", "")):,}`\nTheme: **{self.game["theme"].capitalize()}**', color=get_setting('settings', 'embed_color'))
                embed.add_field(name='__Current letters__', value=' '.join(self.wordVisual), inline=True)
                embed.add_field(name='__Guesses__', value=', '.join(self.guesses).upper() if len(self.guesses) > 0 else 'None', inline=True)
                embed.set_image(f'assets/img/fun/hangman/{self.mistakes}.png')
                embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
                
                await ctx.edit_response(embed, components=[])
                self.stop()
            else:
                await ctx.edit_response(embed, components=self.build())
            
            return
    
    @miru.text_select(
        custom_id='number_select_1',
        placeholder='Numbers from 0-9',
        options=[
            miru.SelectOption(label='0️⃣', description='Zero', value='0'),
            miru.SelectOption(label='1️⃣', description='One', value='1'),
            miru.SelectOption(label='2️⃣', description='Two', value='2'),
            miru.SelectOption(label='3️⃣', description='Three', value='3'),
            miru.SelectOption(label='4️⃣', description='Four', value='4'),
            miru.SelectOption(label='5️⃣', description='Five', value='5'),
            miru.SelectOption(label='6️⃣', description='Six', value='6'),
            miru.SelectOption(label='7️⃣', description='Seven', value='7'),
            miru.SelectOption(label='8️⃣', description='Eight', value='8'),
            miru.SelectOption(label='9️⃣', description='Nine', value='9'),
        ],
        row=3
    )
    async def select_number_1(self, select: miru.TextSelect, ctx: miru.Context):
        number = select.values[0]
        
        if number in self.guesses: # if player guessed that letter already
            embed = hikari.Embed(description='This letter has already been guessed!', color=get_setting('settings', 'embed_error_color'))
            await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
            return
        
        try: # cycle turns
            self.guesser = next(self.guesserIter)[1]
        except:
            self.guesserIter = iter(self.game['guessers'].items())
            self.guesser = next(self.guesserIter)[1]
        
        if number not in self.charIndex:
            self.mistakes = self.mistakes + 1
            self.guesses.append(number)
            
            embed = hikari.Embed(title=f"Incorrect! It's {self.guesser['name']} Turn!", description=f'`{ctx.user.global_name} has guessed number {number}.`\n\nHost: <@{self.author}>\nGuessers: {", ".join(self.game["guessers"])}\nWord Count: `{len(self.game["word"].replace(" ", "")):,}`\nTheme: **{self.game["theme"].capitalize()}**', color=get_setting('settings', 'embed_color'))
            embed.add_field(name='__Current letters__', value=' '.join(self.wordVisual), inline=True)
            embed.add_field(name='__Guesses__', value=', '.join(self.guesses).upper() if len(self.guesses) > 0 else 'None', inline=True)
            embed.set_image(f'assets/img/fun/hangman/{self.mistakes}.png')
            embed.set_thumbnail(self.guesser['url'])

            if self.mistakes != 7:
                await ctx.edit_response(embed, components=self.build())
            else:
                embed = hikari.Embed(title=f"Incorrect, the word was {self.game['word'].capitalize()}! {self.game['author']} wins!", description=f'`{ctx.user.global_name} has guessed number {number}.`\n\nHost: <@{self.author}>\nGuessers: {", ".join(self.game["guessers"])}\nWord Count: `{len(self.game["word"].replace(" ", "")):,}`\nTheme: **{self.game["theme"].capitalize()}**', color=get_setting('settings', 'embed_color'))
                embed.add_field(name='__Current letters__', value=' '.join(self.wordVisual), inline=True)
                embed.add_field(name='__Guesses__', value=', '.join(self.guesses).upper() if len(self.guesses) > 0 else 'None', inline=True)
                embed.set_image(f'assets/img/fun/hangman/{self.mistakes}.png')
                embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
                
                await ctx.edit_response(embed, components=[])
            
            return
        else:
            index = self.charIndex[number]
        
            for i in index:
                self.wordVisual[i] = number
        
            embed = hikari.Embed(title=f"Correct! It's {self.guesser['name']} Turn!", description=f'`{ctx.user.global_name} has guessed number {number}.`\n\nHost: <@{self.author}>\nGuessers: {", ".join(self.game["guessers"])}\nWord Count: `{len(self.game["word"].replace(" ", "")):,}`\nTheme: **{self.game["theme"].capitalize()}**', color=get_setting('settings', 'embed_color'))
            embed.add_field(name='__Current letters__', value=' '.join(self.wordVisual), inline=True)
            embed.add_field(name='__Guesses__', value=', '.join(self.guesses).upper() if len(self.guesses) > 0 else 'None', inline=True)
            embed.set_image(f'assets/img/fun/hangman/{self.mistakes}.png')
            embed.set_thumbnail(self.guesser['url'])
        
            if r'''\_''' not in self.wordVisual:
                embed = hikari.Embed(title=f"Correct! The guessing team wins!", description=f'`{ctx.user.global_name} has guessed number {number}.`\n\nHost: <@{self.author}>\nGuessers: {", ".join(self.game["guessers"])}\nWord Count: `{len(self.game["word"].replace(" ", "")):,}`\nTheme: **{self.game["theme"].capitalize()}**', color=get_setting('settings', 'embed_color'))
                embed.add_field(name='__Current letters__', value=' '.join(self.wordVisual), inline=True)
                embed.add_field(name='__Guesses__', value=', '.join(self.guesses).upper() if len(self.guesses) > 0 else 'None', inline=True)
                embed.set_image(f'assets/img/fun/hangman/{self.mistakes}.png')
                embed.set_thumbnail(ctx.user.avatar_url if ctx.user.avatar_url != None else ctx.user.default_avatar_url)
                
                await ctx.edit_response(embed, components=[])
                self.stop()
            else:
                await ctx.edit_response(embed, components=self.build())
            
            return
    
    async def view_check(self, ctx: miru.Context) -> bool:
        return ctx.user.id == self.guesser['id']
    
## Definitions ##

def load(bot):
    bot.add_plugin(plugin)