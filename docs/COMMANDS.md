# Command list
><> = required, [] = optional

## General
|	Command	| description	| Usage
|---------------|--------------------|--------------|
| help	|	Displays the help menu.	|	`help`	|
| ping	|	Displays bot's latency.	|	`ping`	|
| profile	|	Get info on a server member.	|	`profile [user]`	|


## Economy
|	Command	| description	| Usage
|---------------|--------------------|--------------|
| leaderboard	|	Displays leaderboard rankings.	|	`leaderboard`	|
| balance	|	Get balance of a server member.	|	`balance [user]`	|
| daily	|	Get your daily reward!	|	`daily`	|
| pay	|	Give a server member money.	|	`pay [amount] [user]`	|
| coinflip	|	Flips a coin.	|	`coinflip <amount>`	|
| draw	|	Draw cards from a deck.	|	`draw`	|
| russian-roulette	|	Play a game of Russian Roulette.	|	`russian-roulette <capacity> <bet>`	|
| rps	|	Play a game of Rock-Paper-Scissors.	|	`rps <user> <bet> <wins>`	|
| connect4	|	Play a game of Connect Four.	|	`connect4 <user> <bet>`	|
| blackjack	|	Play a game of Blackjack.	|	`blackjack <bet>`	|


## Music
|	Command	| description	| Usage
|---------------|--------------------|--------------|
| join	|	Makes the bot join your voice channel.	|	`song join`	|
| leave	|	Makes the bot disconnect from your voice channel.	|	`song leave`	|
| play	|	Play a song.	|	`song play <link / song name>`	|
| controller	|	Manage music player options.	|	`song controller <option>`	|
| queue	|	Displays the queue.	|	`song controller queue`	|
| pause	|	Pauses the music.	|	`song controller pause`	|
| skip	|	Skips the current song.	|	`song controller skip`	|
| shuffle	|	Shuffles the playlist.	|	`song controller shuffle`	|
| loop	|	Loops the song or queue.	|	`song controller loop`	|
| clear	|	Clears the playlist.	|	`song controller clear`	|


## Pokémon
|	Command	| description	| Usage
|---------------|--------------------|--------------|
| shop	|	Open the PokéShop menu.	|	`shop`	|
| inventory open	|	Open a server member's inventory.	|	`inventory open [user]`	|
| inventory sell	|	Sell your cards.	|	`inventory sell`	|
| open	|	Open a card pack.	|	`open <uuid>`	|
| info	|	View additional info on a card or pack.	|	`info <uuid>`	|
| trade	|	Trade items or cards with a server member.	|	`trade <user>`	|


## Rushsite
|	Command	| description	| Usage
|---------------|--------------------|--------------|
| register	|	Register now for the latest Rushsite tournament!	|	`rushsite register`	|
| search	|	Get info about this player or team.	|	`rushsite search <player / team>`	|
| top	|	Get the top 10 player based on chosen stat.	|	`rushsite top <stat>`	|
| strike	|	Choose a map by taking turns eliminating maps one by one.	|	`rushsite strike <user> <user>`	|


## Fun
|	Command	| description	| Usage
|---------------|--------------------|--------------|
| random	|	Get something random!	|	`random <option>`	|
| fact	|	Get the useless fact of the day.	|	`fact`	|
| wotd	|	Get the word of the day	|	`wotd`	|
| bored	|	Get an activity suggestion from the bot.	|	`bored`	|
| hangman	|	Play a game of Hangman.	|	`hangman <word> <theme>`	|


## Moderation
|	Command	| description	| Usage
|---------------|--------------------|--------------|
| announce |	Make the bot say something!	|	`admin announce <channel> <ping> [image]`	|
| poll	|	Create a custom poll!	|	`admin poll <title> <options> <timeout> [description] [image]`	|
| poll close	|	Close an existing poll!	|	`admin close-poll <channel> <message_id>`	|
| purge	|	Purge messages from this channel.	|	`admin purge <amount>`	|
| bet	|	Start a live interactive bet!	|	`admin bet <name> <blue> <green> <timeout>`	|
| eco-set	|	Set a server member's wallet to a specific amount.	|	`admin eco-set <user> <amount>`	|
| eco-add	|	Add coins to a server member's wallet.	|	`admin eco-add <user> <amount> <update>`	|
| eco-take |	Remove coins from a server member's wallet.	|	`admin eco-take <user> <amount> <update>`	|
