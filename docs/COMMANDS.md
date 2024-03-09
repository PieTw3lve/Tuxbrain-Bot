# Command list

> <> = required, [] = optional

## General

| Command   | description                                              | Usage                                 |
| --------- | -------------------------------------------------------- | ------------------------------------- |
| help      | Displays the help menu.                                  | `help`                                |
| ping      | Displays bot's latency.                                  | `ping`                                |
| profile   | Retrieve information about yourself or a Discord member. | `profile [user]`                      |
| customize | Customize your profile!                                  | `customize <banner> <base> <nametag>` |
| shop      | Spend coins or tux passes on profile customization.      | `shop`                                |

## Economy

| Command          | description                                                       | Usage                               |
| ---------------- | ----------------------------------------------------------------- | ----------------------------------- |
| blackjack        | Try your luck in a game of Blackjack against a computer.          | `blackjack <bet>`                   |
| coinflip         | Flip a coin.                                                      | `coinflip <amount>`                 |
| connect4         | Engage in a Connect Four game with fellow Discord users.          | `connect4 <user> <bet>`             |
| daily            | Claim your daily reward!                                          | `daily`                             |
| draw             | Draw cards from a deck.                                           | `draw`                              |
| leaderboard      | View economy leaderboard rankings.                                | `leaderboard`                       |
| pay              | Transfer coins to a fellow Discord member.                        | `pay [amount] [user]`               |
| rps              | Challenge a Discord member to a game of Rock-Paper-Scissors.      | `rps <user> <bet> <wins>`           |
| russian-roulette | Engage in a game of Russian Roulette with fellow Discord members. | `russian-roulette <capacity> <bet>` |

## Music

| Command    | description                                       | Usage                          |
| ---------- | ------------------------------------------------- | ------------------------------ |
| join       | Makes the bot join your voice channel.            | `song join`                    |
| leave      | Makes the bot disconnect from your voice channel. | `song leave`                   |
| play       | Play a song.                                      | `song play <link / song name>` |
| queue      | Displays the queue.                               | `song queue`                   |
| controller | Manage music player options.                      | `song controller <option>`     |
| pause      | Pauses the music.                                 | `song controller pause`        |
| skip       | Skips the current song.                           | `song controller skip`         |
| shuffle    | Shuffles the playlist.                            | `song controller shuffle`      |
| loop       | Loops the song or queue.                          | `song controller loop`         |
| clear      | Clears the playlist.                              | `song controller clear`        |

## Pokémon

| Command      | description                                                  | Usage                 |
| ------------ | ------------------------------------------------------------ | --------------------- |
| pokeshop     | Access the PokéShop menu.                                    | `pokeshop`            |
| pokeinv open | Open a server member's inventory.                            | `pokeinv open [user]` |
| pokeinv sell | Sell your cards.                                             | `pokeinv sell`        |
| pokeopen     | Unbox a Pokémon card pack.                                   | `pokeopen <uuid>`     |
| pokeinfo     | Obtain additional details on a Pokémon card or pack.         | `pokeinfo <uuid>`     |
| poketrade    | Initiate a Pokémon item or card trade with a Discord member. | `poketrade <user>`    |

## Rushsite

| Command        | description                                               | Usage                                               |
| -------------- | --------------------------------------------------------- | --------------------------------------------------- |
| register       | Register now for the latest Rushsite tournament!          | `rushsite register`                                 |
| search         | Get info about this player or team.                       | `rushsite search <player / team>`                   |
| top            | Get the top 10 player based on chosen stat.               | `rushsite top <stat>`                               |
| strike         | Choose a map by taking turns eliminating maps one by one. | `rushsite-admin strike <maps> <user> <user> <mode>` |
| generate-pools | Generates randomized pools of teams from a given list.    | `rushsite-admin generate-pools <teams> <groups>`    |

## Fun

| Command | description                                                          | Usage                    |
| ------- | -------------------------------------------------------------------- | ------------------------ |
| random  | Retrieve a random item or information.                               | `random <option>`        |
| fact    | Retrieve the useless fact of the day.                                | `fact`                   |
| wotd    | Retrieve the Word of the Day                                         | `wotd`                   |
| bored   | Receive a suggested activity from the bot.                           | `bored`                  |
| hangman | Engage in a competitive game of Hangman with fellow Discord members. | `hangman <word> <theme>` |

## Moderation

| Command          | description                                                  | Usage                                                    |
| ---------------- | ------------------------------------------------------------ | -------------------------------------------------------- |
| broadcast        | Command the bot to deliver a message!                        | `broadcast <channel> <ping> [image]`                     |
| poll             | Create a customizable poll.                                  | `poll <title> <options> <timeout> [description] [image]` |
| poll close       | End an ongoing poll.                                         | `close-poll <channel> <message_id>`                      |
| purge            | Remove messages from a Discord channel.                      | `purge <amount>`                                         |
| start-prediction | Initiate a live interactive bet for users to participate in. | `start-prediction <name> <blue> <green> <timeout>`       |
| wallet set       | Set a server member's wallet to a specific amount.           | `wallet set <user> <amount>`                             |
| wallet add       | Add coins to a server member's wallet.                       | `wallet add <user> <amount> <update>`                    |
| wallet take      | Remove coins from a server member's wallet.                  | `wallet take <user> <amount> <update>`                   |
| ticket set       | Set a server member's wallet to a specific amount.           | `ticket set <user> <amount>`                             |
| ticket add       | Add coins to a server member's wallet.                       | `ticket add <user> <amount> <update>`                    |
| ticket take      | Remove coins from a server member's wallet.                  | `ticket take <user> <amount> <update>`                   |
