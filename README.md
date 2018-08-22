# ThePokeGOBot
A Pokémon GO Telegram bot to manage raids and quests.
## Requirements
- [Python 3.6+](https://www.python.org/downloads/)
- [Telepot](https://github.com/nickoala/telepot)
- [Emoji](https://github.com/carpedm20/emoji/)

## Installation
1. Install Python 3.6+
2. Install the requirements
`python -m pip install -r requirements.txt`
4. Create a Telegram bot using [BotFather](https://telegram.me/botfather) and get its token
3. Edit the `config.json` by replacing the following:

- `BOT_TOKEN` with your Telegram Bot Token
- `123456` with your Telegram ID (some commands will only respond to this ID), that can be found by starting a conversation with [this bot](https://telegram.me/getidsbot)
- `en` with any of the available languages (one of the folder names inside `/locale` directory). If empty or set to an unavailable language it will be set to the main language (English).
- `YOUR_USERNAME` with your Telegram username
5. Run the bot by using `python launcher.py`
6. Add the bot to a supergroup and give it administrator rights
7. Enjoy the bot!

## Localization
It's possible to translate the bot to your own language. To do so, follow this steps:

1. Download [POEdit](https://poedit.net/)
2. Open the file `launcher.py.pot` with POEdit
3. Click on `Create new translation` and choose the desided language
4. Translate each of the bot's sentence
5. Save the file and place it inside `locale`, following the pattern of the `locale\en` folder
6. Change the `config.json` file by replacing the `language` parameter to the name of the folder you just created on the step above
7. Start the bot

## Commands
*This are the commands when using the English version of the bot. You can change them (or not) by translating the bot to your own language.*

|    Command   	|  Permission 	| Function 	| Usage 	|
|---------------|---------------|-----------|-----------|
| /help         | All members   |show a help message|`/help`|
| /trainer     	| All members 	|set your team and level|`/trainer initial letter/team name/color 30`|
| /level       	| All members 	|update your level but only works after the /trainer command has already been used|`/level 31`|
| /raid        	| All members 	|starts a new raid's list|`/raid pokémon,place,HH:MM`|
| /edit        	| All members 	|change the time of a on going raid's list|`/edit raid's ID HH:MM`|
| /cancel      	| All members 	|cancel a on going raid's list|`/cancel raid's ID`|
| /end         	| All members 	|finish a on going raid's list|`/end raid's ID`|
| /quest       	| All members 	|report a found quest|`/quest task,place,reward`|
| /share       	| All members 	|send a raid's list or quest's report to another group so that both are automatically updated in the groups it was shared to|`/share q/r raid's/quest's ID`|
| /comment     	| All members 	|add informations to a raid's list or quest's report|`/comment q/r raid's/quest's ID comment`|
| /setraids    	| Master only 	|set the current available raids in the game|`/setraid pkmn_number,pkmn_number`|
| /getraids    	| Master only 	|get the list of current available raids in the game|`/getraids`|
| /gettrainers 	| Master only 	|get the list of users that have set their trainer's information|`/gettrainers`|

## TODO
- Only create raid's list with time in the future
- ~~Create raid's list by using the Pokémon Pokédex Number~~
- ~~Create raid's list for raids that are yet to hatch~~
- ~~Edit raid list's raid boss~~
~~- Cancel quests~~
