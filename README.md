<h1 align="center">Tuxbrain Bot</h1>

<p align="center">
	<img alt="GitHub Release" src="https://img.shields.io/github/v/release/PieTw3lve/Tuxbrain-Bot?display_name=tag&style=for-the-badge&label=Release">
	<img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/PieTw3lve/Tuxbrain-Bot/python-app.yml?style=for-the-badge&logo=GitHub"> 
	<a href="https://discord.gg/KdgecRyHMM"><img src="https://img.shields.io/discord/800088413373333544?style=for-the-badge&logo=Discord&color=%237289da" alt="License"></a>
	<a href="https://www.gnu.org/licenses/gpl-3.0"><img src="https://img.shields.io/badge/License-GPLv3-yellow.svg?style=for-the-badge" alt="License"></a>
</p>

Tuxbrain Bot is an open source, multi-use Discord bot written in hikari.py, a new static-typed Python API wrapper. The bot is currently still in development, so there may be some bugs. Although it was designed for Tuxbrain.org servers, the bot can be hosted and used on any server.

### Features

- Profile Customization: `profile`, `set`, `shop`!
- Economy Integration: `leaderboard`, `daily`, `pay`, and **6** more!
- Music Player: `play`, `controller`, `join`, and `leave`!
- Pokémon Card Collecting and Trading: `pokeshop`, `pokeinv`, `pokeopen`, `pokeinfo`, and `poketrade`!
- Interactive Games: `russian-roulette`, `rps`, `connect4`, `blackjack`, and `hangman`!
- Tuxbrain Rushsite Integration: `register`, `search`, `top`, and `strike`!
- Moderation: `broadcast`, `poll`, `purge`, `translator` and **6** more!
- Fun/Useless Commands: `random`, `fact`, and `wotd`!

### Installation

1. Clone the repository to your local machine.

```
git clone https://github.com/PieTw3lve/Tuxbrain-Bot.git
```

2. Install the required dependencies.

```
pip install -r requirements.txt --no-dependencies
```

3. Set up and operate a [Lavalink](https://github.com/lavalink-devs/Lavalink) server to enable music playback.

```
cd Lavalink
java -jar Lavalink.jar
```

### How to run the Bot

> [!IMPORTANT]  
> Tuxbrain Bot requires Python 3.11.0 or later to run.

1. Generate settings.json by running the bot.py file once.
2. Fill in the settings.json file with your bot token, guild ids, and other necessary information.
3. Enable all intents through the [Discord Developer Portal](https://discord.com/developers/applications).
4. Run the bot.py file again to start the bot.

```
cd src
python3.11 -O bot.py
```

### Further readings

- Hikari: https://github.com/hikari-py/hikari
- Lightbulb: https://github.com/tandemdude/hikari-lightbulb
- Miru: https://github.com/HyperGH/hikari-miru
- Lavalink: https://github.com/Devoxin/Lavalink.py
- Deep Translator: https://github.com/nidhaloff/deep-translator#chatgpt-translator
- Lingua: https://github.com/pemistahl/lingua-py
