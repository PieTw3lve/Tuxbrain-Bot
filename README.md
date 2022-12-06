## Description
Tux Bot is an open source, multi-use bot programmed by Pie12#1069. Tux Bot is written in [hikari.py](https://www.hikari-py.dev/), a new static-typed Python API for writing Discord Bot. Which means it is still in an alpha state, so expect some minor bugs! This bot is specifically for the Tux servers. However, feel free to run this bot for your personal use. Please check the license before performing any actions related to this bot. 

Shoutouts to **Ryan#3388** and **BoboTheChimp#6164** for helping!

## Requirements
You will need to install a few dependencies in order for the Bot to function correctly. Run these commands in your console to install.

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
#### Note: Miru is currently not supported with Python 3.11+ 
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
If you haven't already, you need to edit the `startup.py` file and enter your Bot's token and your server's guild ID. Make sure to enable all intents through the [Discord Developer Portal](https://discord.com/developers/applications). Finally, run the bot.py file through console and you're set!

## Further reading

- Hikari: https://github.com/hikari-py/hikari
- Lightbulb: https://github.com/tandemdude/hikari-lightbulb
- Miru: https://github.com/HyperGH/hikari-miru
- Google Translate: https://github.com/ssut/py-googletrans
