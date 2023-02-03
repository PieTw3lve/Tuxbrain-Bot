## Description
Tux Bot is an open source, multi-use bot programmed by **Pie12#1069**. Tux Bot is written using [hikari.py](https://www.hikari-py.dev/), a new static-typed Python API for writing Discord Bot. Which means it is still in an alpha state, so expect some minor bugs! This bot is specifically for the Tux servers. However, feel free to run this bot for your personal use. Please check the license before performing any actions related to this bot. 

## Features

- Customized Discord User Profiles 
- Economy Manager and Interactable Games (Gambling!)
- A Full Fledged out RPG System
- Tux Rushsite Integration
- Automatic Text Translation
- OpenAI Integration
- Fun/Useless Commands
- And Many More!

## Installation
You will need to install a few dependencies for the Bot to function appropriately. Fortunately, there is a convenient way to install these dependencies using only one command. This method requires the `requirements.txt` file included above. You can use it by running the first command below. However, if that method does not work, it is mandatory to install each dependency separately.

### Requirements.txt
You need Python version **3.11.0+** to install the pre-requisites.

```
pip install -r requirements.txt
```

### Hikari

```
python -m pip install -U hikari
# Windows users may need to run this instead...
py -3 -m pip install -U hikari
```

### Lightbulb

```
python3 -m pip install -U hikari-lightbulb
# Windows users may need to run this instead...
py -3 -m pip install -U hikari-lightbulb
```

### Miru

```
python3 -m pip install -U hikari-miru
# Windows users may need to run this instead...
py -3 -m pip install -U hikari-miru
```

### Google Translate

```
python3 -m pip install -U googletrans-py
# Windows users may need to run this instead...
py -3 -m pip install -U googletrans-py
```

## How do I run this Bot?
If you haven't already, you need to edit the `startup.py` file and enter your Bot's token and your server's guild ID. Make sure to enable all intents through the [Discord Developer Portal](https://discord.com/developers/applications). Finally, run the `bot.py` file through console and you're set!

## Further readings

- Hikari: https://github.com/hikari-py/hikari
- Lightbulb: https://github.com/tandemdude/hikari-lightbulb
- Miru: https://github.com/HyperGH/hikari-miru
- Google Translate: https://github.com/ssut/py-googletrans
