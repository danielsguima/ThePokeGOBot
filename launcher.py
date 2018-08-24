import gettext
import sys
import asyncio
from datetime import date, datetime, timezone, timedelta
import time
import json
import emoji
import telepot
from telepot.aio.loop import MessageLoop
from telepot.aio.delegate import (
    per_chat_id, create_open, pave_event_space, include_callback_query_chat_id)
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton


class ThePokeGOBot(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, **kwargs):
        super(ThePokeGOBot, self).__init__(*args, **kwargs)

        self.load_data()

        self.router.routing_table['_delete_raid'] = self.on___delete_raid
        self.router.routing_table['_delete_quest'] = self.on___delete_quest
        self.router.routing_table['_delete_help'] = self.on___delete_help
        self.router.routing_table['_delete_bot_messages'] = self.on___delete_bot_messages

    async def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)

        user = msg['from']

        if content_type != 'text':
            return

        command = msg['text'].strip().lower()

        if(command.startswith('/')):
            message = command.split(' ')
            command = message[0].strip()
            del message[0]
            params = message
            await self.handle_command(command, params, user, msg)

    async def handle_command(self, cmd, params, user, user_msg):
        self.load_data()

        # Start a raid
        if cmd == _('/raid'):
            parts = " ".join(params).split(',')

            if len(parts) == 3:
                try:
                    if parts[0].strip().title() in self.pokemon:
                        pkmn_num = self.pokemon.index(
                            parts[0].strip().title()) + 1
                        pkmn_name = parts[0].strip().title()
                    elif parts[0].strip().title() in self.levels:
                        pkmn_num = parts[0].strip().title()
                        pkmn_name = pkmn_num
                    else:
                        try:
                            pkmn_num = int(parts[0].strip().title())
                            pkmn_name = self.pokemon[pkmn_num - 1]
                        except TypeError:
                            msg = await self.sender.sendMessage(_("Meowth! *%s* is not a valid Pokémon!") % (parts[0].strip().title()), parse_mode="markdown")
                            self.delete_messages(msg)

                    if pkmn_num in self.curr_raids:
                        try:
                            if self.is_time_in_future(parts[2].strip()):
                                raid = {
                                    'id': int(self.raids['index']) + 1,
                                    'pokemon': pkmn_name.title(),
                                    'place': parts[1].strip().title(),
                                    'start_time': parts[2].strip(),
                                    'created_by': user,
                                    'status': _('active'),
                                    'going': [],
                                    'messages': [],
                                    'comments': []
                                }

                                raid_keyboard = self.create_keyboard(raid)

                                msg = await self.sender.sendMessage(self.create_list(raid), reply_markup=raid_keyboard, parse_mode="markdown")

                                self.scheduler.event_later(self.convert_to_seconds(
                                    1, 45), ('_delete_raid', {'raid_id': raid['id']}))

                                if next((x for x in raid['messages'] if int(x['message_id']) == int(msg['message_id'])), None) == None:
                                    raid['messages'].append(msg)

                                self.raids["index"] = int(raid['id'])
                                self.raids["raids"].append(raid)
                                self.persist_data()
                            else:
                                msg = await self.sender.sendMessage(_("Meowth! The time must be in the future!"), parse_mode="markdown")
                                self.delete_messages(msg)
                        except Exception:
                            msg = await self.sender.sendMessage(_("Meowth! The time must be in the format of *HH:MM*!"), parse_mode="markdown")
                            self.delete_messages(msg)
                    else:
                        msg = await self.sender.sendMessage(_("Meowth! The Pokémon *%s* is not currently in the raids!") % (parts[0].strip().title()), parse_mode="markdown")
                        self.delete_messages(msg)
                except:
                    msg = await self.sender.sendMessage(_("Meowth! *%s* is not a valid Pokémon!") % (parts[0].strip().title()), parse_mode="markdown")
                    self.delete_messages(msg)
        # Edit the start time of the raid
        elif cmd == _('/edit'):
            if len(params) == 3:
                can_edit = False

                raid_id = int(params[0])
                new_time = params[1].strip()
                new_poke = params[2].strip().title()

                raid = next(
                    (x for x in self.raids['raids'] if int(x['id']) == raid_id), None)
                if raid == None:
                    msg = await self.sender.sendMessage(_("Meowth! The raid of id *%s* does not exist or has already ended!") % (raid_id))
                    self.delete_messages(msg)
                else:
                    if user['id'] == raid['created_by']['id'] or user['id'] == self.master:
                        try:
                            self.pokemon.index(new_poke) + 1
                            can_edit = True
                        except Exception:
                            try:
                                if int(new_poke) in self.curr_raids:
                                    can_edit = True
                                    new_poke = self.pokemon[int(new_poke) - 1]
                                else:
                                    msg = await self.sender.sendMessage(_("Meowth! *%s* is not a valid Pokémon!") % (new_poke), parse_mode="markdown")
                                    self.delete_messages(msg)
                                    can_edit = False
                            except TypeError:
                                if new_poke in self.curr_raids:
                                    can_edit = True
                                else:
                                    msg = await self.sender.sendMessage(_("Meowth! *%s* is not a valid Pokémon!") % (new_poke), parse_mode="markdown")
                                    self.delete_messages(msg)
                                    can_edit = False
                        
                        try:
                            if self.is_time_in_future(new_time):
                                can_edit = True
                            else:
                                msg = await self.sender.sendMessage(_("Meowth! The time must be in the future!"), parse_mode="markdown")
                                self.delete_messages(msg)
                                can_edit = False
                        except Exception:
                            msg = await self.sender.sendMessage(_("Meowth! The time must be in the format of *HH:MM*!"), parse_mode="markdown")
                            self.delete_messages(msg)
                            can_edit = False

                        if can_edit == True:
                            raid['start_time'] = new_time
                            raid['pokemon'] = new_poke
                            self.persist_data()
                            for msg in raid['messages']:
                                await self.bot.editMessageText(telepot.message_identifier(msg), self.create_list(raid), reply_markup=self.create_keyboard(raid), parse_mode="markdown")
        # Cancel/finish active raid
        elif cmd == _('/cancel') or cmd == _('/end'):
            if len(params) == 2:
                if params[0] == _('r'):
                    command = _('cancel') if cmd == _('/cancel') else _('end')
                    raid_id = params[1].strip()

                    if raid_id:
                        raid = next((x for x in self.raids['raids'] if int(
                            x['id']) == int(raid_id)), None)
                        if raid == None:
                            msg = await self.sender.sendMessage(_("Meowth! The raid of id *%s* does not exist or has already ended!") % (raid_id), parse_mode="markdown")
                            self.delete_messages(msg)
                        else:
                            if raid['created_by']['id'] == user['id'] or user['id'] == self.master:
                                raid['status'] = _('canceled') if command == _(
                                    'cancel') else _('ended')
                                self.persist_data()
                                for msg in raid['messages']:
                                    await self.bot.editMessageText(telepot.message_identifier(msg), self.create_list(raid), reply_markup=None, parse_mode="markdown")
                elif params[0] == _('q') and cmd == _('/cancel'):
                    quest_id = params[1].strip()

                    if quest_id:
                        quest = next((x for x in self.quests['quests'] if int(
                            x['id']) == int(quest_id)), None)

                        if quest == None:
                            msg = await self.sender.sendMessage(_("Meowth! The quest of id *%s* does not exist!") % (raid_id), parse_mode="markdown")
                            self.delete_messages(msg)
                        else:
                            if quest['created_by']['id'] == user['id'] or user['id'] == self.master:
                                quest['status'] = _('canceled')
                                self.persist_data()
                                for msg in quest['messages']:
                                    self.delete_messages(msg, 0)
        # Set trainer informations
        elif cmd == _('/trainer'):
            teams = [['valor', _('red'), 'v', ':fire:'], [
                'mystic', _('blue'), 'm', ':snowflake:'], ['instinct', _('yellow'), 'i', '⚡']]

            trainer = {}
            trainer_team = None
            for p in params:
                i = 0
                for t in range(0, 3):
                    if p in teams[t]:
                        trainer['team'] = f"{teams[i][0]}"
                        trainer['emoji'] = f"{emoji.emojize(teams[i][3])}"
                        trainer_team = f"{trainer['team']} ({teams[i][1]})"
                        break
                    else:
                        i += 1

                try:
                    level = int(p)
                    if level > 0 and level <= 40:
                        trainer['level'] = level
                except:
                    continue

            if 'team' in trainer and 'level' in trainer:
                trainer['id'] = user['id']
                if next((x for x in self.trainers if int(x['id']) == int(user['id'])), None) == None:
                    self.trainers.append(trainer)
                else:
                    i = 0
                    for x in self.trainers:
                        if int(x['id']) == int(user['id']):
                            self.trainers.pop(i)
                            self.trainers.append(trainer)
                            break
                        else:
                            i += 1

                self.persist_data()
                msg = await self.sender.sendMessage(_("Meowth! Team *%s* and level *%s* set!") % (trainer_team.title(), trainer['level']), parse_mode="markdown")
                self.delete_messages(msg)
            else:
                msg = await self.sender.sendMessage(_("Meowth! Input a valid team and level!"))
                self.delete_messages(msg)
        # Update trainer's level
        elif cmd == _('/level'):
            if len(params) == 1:
                level = int(params[0].strip())

                if level:
                    trainer = next((x for x in self.trainers if int(
                        x['id']) == int(user['id'])), None)
                    if trainer != None:
                        if level > 0 and level <= 40:
                            trainer['level'] = level
                            self.persist_data()
                            msg = await self.sender.sendMessage(_("Meowth! Your level was updated to *%s*!") % (level), parse_mode="markdown")
                            self.delete_messages(msg)
                        else:
                            msg = await self.sender.sendMessage(_("Meowth! Input a valid level!"))
                            self.delete_messages(msg)
                    else:
                        msg = await self.sender.sendMessage(_("Meowth! Set up your informations using */trainer team level*! This command is only for updating your level after your trainer's info are all set up!"), parse_mode="markdown")
                        self.delete_messages(msg)
        # Post a quest report
        elif cmd == _('/quest'):
            parts = " ".join(params).split(',')

            if len(parts) == 3:
                quest = {
                    'id': int(self.quests['index']) + 1,
                    'quest': parts[0].strip().title(),
                    'place': parts[1].strip().title(),
                    'reward': parts[2].strip().title(),
                    'created_by': user,
                    'status': _('active'),
                    'messages': [],
                    'comments': []
                }

                msg = await self.sender.sendMessage(self.create_quest(quest), parse_mode="markdown")

                now = datetime.now().astimezone(self.timezone)
                tomorrow = datetime(now.year, now.month,
                                    now.day + 1, tzinfo=self.timezone)
                diff = (tomorrow - now).seconds

                self.scheduler.event_later(
                    diff, ('_delete_quest', {'quest_id': quest['id']}))

                if next((x for x in quest['messages'] if int(x['message_id']) == int(msg['message_id'])), None) == None:
                    quest['messages'].append(msg)

                self.quests['index'] = int(quest['id'])
                self.quests['quests'].append(quest)
                self.persist_data()
        # Share/comment raid/quest
        elif cmd == _('/share') or cmd == _('/comment'):
            if len(params) >= 2:
                try:
                    _id = int(params[1].strip())
                    _type = _("raid or quest")
                    obj = {}
                    _list = []
                    command = _(
                        '/share') if cmd == _('/share') else _('/comment')

                    if _id:
                        if params[0].strip().lower() == _('r'):
                            _list = self.raids["raids"]
                            _type = _("raid")
                        elif params[0].strip().lower() == _('q'):
                            _list = self.quests["quests"]
                            _type = _("quest")
                        else:
                            msg = await self.sender.sendMessage(_("Meowth! Invalid command!"))
                            self.delete_messages(msg)

                        obj = next((x for x in _list if int(
                            x['id']) == int(_id)), None)
                        if obj == None:
                            msg = await self.sender.sendMessage(_("Meowth! The %s of id *%s* does not exist or has already ended!") % (_type, _id), parse_mode="markdown")
                            self.delete_messages(msg)
                        else:
                            if command == _('/share'):
                                if obj['status'] == _('active'):
                                    if params[0] == _('r'):
                                        msg = await self.sender.sendMessage(self.create_list(obj), reply_markup=self.create_keyboard(obj), parse_mode="markdown")
                                    elif params[0] == _('q'):
                                        msg = await self.sender.sendMessage(self.create_quest(obj), parse_mode="markdown")

                                    if next((x for x in obj['messages'] if int(x['chat']['id']) == int(msg['chat']['id'])), None) != None:
                                        await self.bot.deleteMessage(telepot.message_identifier(msg))
                                        msg = await self.sender.sendMessage(_("Meowth! The %s of id *%s* has already been posted in this group!") % (_type, _id), parse_mode="markdown")
                                        self.delete_messages(msg)

                                    if next((x for x in obj['messages'] if int(x['message_id']) == int(msg['message_id'])), None) == None:
                                        obj['messages'].append(msg)
                                        self.persist_data()
                                    else:
                                        await self.bot.deleteMessage(telepot.message_identifier(msg))
                                else:
                                    msg = await self.sender.sendMessage(_("Meowth! The raid of id *%s* has already been ended or canceld!") % (_id))
                            else:
                                add = True

                                if params[0] == _('r'):
                                    add = next((x for x in obj['going'] if int(
                                        x['user']['id']) == int(user['id'])), None) != None

                                if add == True:
                                    message = ""
                                    for word in params:
                                        if params.index(word) >= 2:
                                            message += f"{word.strip()} "
                                    comment = {
                                        'user': user,
                                        'comment': message
                                    }

                                    if next((x for x in obj['comments'] if int(x['user']['id']) == int(user['id'])), None) == None:
                                        obj['comments'].append(comment)
                                    else:
                                        i = 0
                                        for x in obj['comments']:
                                            if int(x['user']['id']) == int(user['id']):
                                                obj['comments'].pop(i)
                                                obj['comments'].append(comment)
                                                break
                                            else:
                                                i += 1

                                    self.persist_data()

                                    for msg in obj['messages']:
                                        if params[0] == _('r'):
                                            await self.bot.editMessageText(telepot.message_identifier(msg), self.create_list(obj), reply_markup=self.create_keyboard(obj), parse_mode="markdown")
                                        else:
                                            await self.bot.editMessageText(telepot.message_identifier(msg), self.create_quest(obj), parse_mode="markdown")
                except:
                    return
        # Help command
        elif cmd == _('/help'):
            await self.help(user_msg)
        # None of the commands
        else:
            if user['id'] != self.master:
                await self.help(user_msg)

        # MASTER commands
        if user['id'] == self.master:
            # Set available raids
            if cmd == _('/setraids'):
                self.curr_raids = []
                error = False
                pkmn_names = []

                for pkmn in params[0].split(','):
                    try:
                        num = int(pkmn.strip())
                        pkmn_names.append(f"*{self.pokemon[num]}*")
                        self.curr_raids.append(num)
                    except:
                        msg = await self.sender.sendMessage(_("Meowth! Input the Pokémon numbers!"))
                        self.delete_messages(msg)
                        error = True
                        break

                if error == False:
                    names = "\n".join(pkmn_names)
                    msg = await self.sender.sendMessage(_("Meowth! Current raids set to:\n\n%s") % (names), parse_mode="markdown")
                    self.delete_messages(msg)
                    self.persist_data()
            # Get available raids
            elif cmd == _('/getraids'):
                message = _("Current raids\n")
                for pkmn in self.curr_raids:
                    try:
                        pkmn = int(pkmn)
                        message += f"\n*{self.pokemon[pkmn]}*"
                    except ValueError:
                        message += f"\n*{pkmn}*"

                msg = await self.sender.sendMessage(message, parse_mode="markdown")
                self.delete_messages(msg)
            # Get registered trainers
            elif cmd == _('/gettrainers'):
                message = _("*Trainers*\n")
                for t in self.trainers:
                    try:
                        member = await self.bot.getChatMember(user_msg['chat']['id'], t['id'])
                        message += f"\n{member['user']['first_name']}"

                        if 'last_name' in member['user']:
                            message += f" {member['user']['last_name']}"

                        message += f" {t['level']} {emoji.emojize(t['emoji'])}"
                    except:
                        continue

                msg = await self.sender.sendMessage(message, parse_mode="markdown")
                self.delete_messages(msg, 10)

        if user_msg['chat']['type'] != 'private':
            self.delete_messages(user_msg, 1)

    async def help(self, user_msg):
        will_delete = _(
            "\n\n_This message will be automatically deleted in a minute._") if user_msg['chat']['type'] != 'private' else ""

        msg = await self.sender.sendMessage(
            _("*Commands*"
              "\n/trainer - set your team and level."
              "\n`/trainer initial letter/team name/color 30`"
              "\n/level - update your level but only works after the /trainer command has already been used."
              "\n`/level 31`"
              "\n/raid - starts a new raid's list."
              "\n`/raid level/pokémon (pokédex number or name),place,HH:MM`"
              "\n/edit - change the time and the Pokémon of a on going raid's list."
              "\n`/edit raid's ID HH:MM Pokémon name`"
              "\n/cancel - cancel a on going raid's list or delete a quest."
              "\n`/cancel r/q raid's/quest's ID`"
              "\n/end - finish a on going raid's list."
              "\n`/end raid's ID`"
              "\n/quest - report a found quest."
              "\n`/quest task,place,reward`"
              "\n/share - send a raid's list or quest's report to another group so that both are automatically updated in the groups it was shared to."
              "\n`/share q/r raid's/quest's ID`"
              "\n/comment - add informations to a raid's list or quest's report."
              "\n`/comment q/r raid's/quest's ID comment`"
              "\n\n*Raid's list*"
              "\nTo add yourself to the list, just tap the _Yes_ button."
              "\nIn case there are more people going with you tap the _+1_ for each extra trainer that is going with you."
              "\nIn case you can no longer go tap the _No_ and your name will be automatically removed."
              "\n\n*Comments*"
              "\nOnly those who confirmed that are going to the raid can comment on it."
              "\nOn quest's report, anyone can comment."
              "\n\n*Report's duration*"
              "\nAfter 1 hour and 45 minutes a raid's list is set to ended (time to egg hatching + raid's duration)."
              "\nAt midnight of each day the quests' reports are deleted."
              "\n\nAny question, talk to %s %s") % (self.master_username, will_delete),
            parse_mode="markdown")

        if user_msg['chat']['type'] != 'private':
            self.scheduler.event_later(60, ('_delete_help', {'message': msg}))

    async def on___delete_bot_messages(self, event):
        await self.bot.deleteMessage(telepot.message_identifier(event['_delete_bot_messages']['delete']))

    async def on___delete_raid(self, event):
        await self.delete_data(event, self.raids['raids'], event['_delete_raid']['raid_id'])

    async def on___delete_quest(self, event):
        await self.delete_data(event, self.quests['quests'], event['_delete_quest']['quest_id'])

    async def on___delete_help(self, event):
        await self.bot.deleteMessage(telepot.message_identifier(event['_delete_help']['message']))

    async def delete_data(self, event, _list, _id):
        obj = next((x for x in _list if int(x['id']) == int(_id)), None)

        if obj != None:
            obj['status'] = _('ended')

            for msg in obj['messages']:
                if 'status' in obj:
                    await self.bot.editMessageText(telepot.message_identifier(msg), self.create_list(obj), parse_mode="markdown")
                else:
                    await self.bot.editMessageText(telepot.message_identifier(msg), self.create_quest(obj), parse_mode="markdown")

            i = 0
            for x in _list:
                if int(x['id']) == int(_id):
                    _list.pop(i)
                    self.persist_data()
                    break
                else:
                    i += 1

    async def on_callback_query(self, msg):
        query_id, from_id, query_data = telepot.glance(
            msg, flavor='callback_query')
        query_data = query_data.split(',')

        raid_id = query_data[0]
        response = query_data[1]

        raid = next((x for x in self.raids['raids'] if int(
            x['id']) == int(raid_id)), None)

        if raid != None:
            user = next((x for x in raid['going'] if int(
                x['user']['id']) == int(msg['from']['id'])), None)
            if response == "yes":
                if user == None:
                    raid['going'].append({
                        "user": msg['from'],
                        "count": 0
                    })
                else:
                    return
            elif response == "no":
                if user != None:
                    raid['going'] = self.remove(
                        raid['going'], msg['from']['id'])

                    i = 0
                    for comment in raid['comments']:
                        if comment['user']['id'] == msg['from']['id']:
                            raid['comments'].pop(i)
                            break
                        else:
                            i = i + 1
                else:
                    return
            else:
                user = next((x for x in raid['going'] if int(
                    x['user']['id']) == int(msg['from']['id'])), None)

                if user != None:
                    user['count'] += 1
                else:
                    raid['going'].append({
                        "user": msg['from'],
                        "count": 1
                    })

            raid_keyboard = self.create_keyboard(raid)
            self.persist_data()

            for msg in raid['messages']:
                message_idf = telepot.message_identifier(msg)
                await self.bot.editMessageText(message_idf, self.create_list(raid), reply_markup=raid_keyboard, parse_mode="markdown")

    def delete_messages(self, msg, after=5):
        self.scheduler.event_later(
            after, ('_delete_bot_messages', {'delete': msg}))

    def mention_member(self, user):
        username = f"{user['first_name']}"
        if 'last_name' in user:
            username += f" {user['last_name']}"

        trainer_info = ""
        trainer = next((x for x in self.trainers if int(
            x['id']) == int(user['id'])), None)
        if trainer != None:
            trainer_info = f" {trainer['level']} {trainer['emoji']}"

        return f"[{username}](tg://user?id={user['id']}){trainer_info}"

    def create_keyboard(self, raid):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=_('Yes'), callback_data=f"{raid['id']},yes"),
             InlineKeyboardButton(
                 text=_('No'), callback_data=f"{raid['id']},no"),
             InlineKeyboardButton(text='+1', callback_data=f"{raid['id']},+1")]
        ])

    def create_quest(self, quest):
        message = _("#️⃣ ID: *%s*\n🕵🏽‍♂️ Quest: *%s*\n%s Place: *%s*\n%s Reward: *%s*") % (
            quest['id'], quest['quest'], emoji.emojize(':round_pushpin:'), quest['place'], emoji.emojize(':trophy:'), quest['reward'])

        if quest['status'] == _('active'):
            if len(quest['comments']) > 0:
                message += _("\n\n*Comments:*")
                for comment in quest['comments']:
                    message += f"\n{self.mention_member(comment['user'])}: {comment['comment']}"

            message += _("\n\n*Reported by:* %s") % (
                self.mention_member(quest['created_by']))
        else:
            message += f"\n\n*{quest['status'].upper()}*"

        return message

    def create_list(self, raid):
        message = _("#️⃣ ID: *%s*\n%s Pokémon: *%s*\n%s Place: *%s*\n%s Time: *%s*") % (raid['id'], emoji.emojize(
            ':trident_emblem:'), raid['pokemon'], emoji.emojize(':round_pushpin:'), raid['place'], emoji.emojize(':alarm_clock:'), raid['start_time'])

        if raid['status'] == _('active'):
            i = 1

            total = len(raid['going'])
            for r in raid['going']:
                total += r['count']

            if total > 0:
                message += _("\n\n*Going:* %s") % (total)

            for x in raid['going']:
                if i == 1:
                    message += "\n"
                message += f"\n{i}. {self.mention_member(x['user'])}"
                i += 1

                total += x['count']

                if x['count'] > 0:
                    message += f" (+{x['count']})"

            if len(raid['comments']) > 0:
                message += _("\n\n*Comments:*")
                for comment in raid['comments']:
                    message += f"\n{self.mention_member(comment['user'])}: {comment['comment']}"

            message += _("\n\n*Created by:* %s") % (
                self.mention_member(raid['created_by']))
        else:
            message += f"\n\n*{raid['status'].upper()}*"

        return message

    def remove(self, _list, id):
        i = 0
        for x in _list:
            if int(x['user']['id']) == int(id):
                _list.pop(i)
                break
            else:
                i += 1

        return _list

    def load_data(self):
        config = json.loads(open('config.json').read())

        self.timezone = timezone(timedelta(hours=config['timezone']))
        self.master = config['master_id']
        self.master_username = config['master_username']

        self.curr_raids = json.loads(open('data/raids.json').read())
        self.pokemon = json.loads(open('data/pokemon.json').read())
        self.levels = json.loads(open('data/levels.json').read())
        self.raids = json.loads(open('data/active_raids.json').read())
        self.trainers = json.loads(open('data/trainers.json').read())
        self.quests = json.loads(open('data/quests.json').read())

    def persist_data(self):
        # save active raids
        self.save_json(self.raids, 'data/active_raids.json')

        # save trainers
        self.save_json(self.trainers, 'data/trainers.json')

        # save quests
        self.save_json(self.quests, 'data/quests.json')

        # save current available raids
        self.save_json(self.curr_raids, 'data/raids.json')

    def save_json(self, obj, filename):
        with open(filename, 'w') as f:
            json.dump(obj, f)

    def convert_to_seconds(self, hours, minutes):
        return int((hours * 3600) + (minutes * 60))

    def is_time_in_future(self, time_str):
        now = datetime.now()

        raid_time = time.strptime(
            time_str, '%H:%M')
        raid_time = datetime(
            now.year, now.month, now.day, raid_time.tm_hour, raid_time.tm_min).time()

        return raid_time >= datetime.now().time()


config = json.loads(open('config.json').read())

language = gettext.translation(
    'thepokegobot', localedir='locale', languages=[config['language']])
language.install()

bot = telepot.aio.DelegatorBot(config['token'], [
    include_callback_query_chat_id(
        pave_event_space())(
            per_chat_id(), create_open, ThePokeGOBot, timeout=600)
])

loop = asyncio.get_event_loop()
loop.create_task(MessageLoop(bot).run_forever())

print(_("Meowth! That's right!"))

loop.run_forever()
