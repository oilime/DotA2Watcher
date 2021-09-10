import json
import os
import sys
import pygtrie
import random
import re
import nonebot

from hoshino import Service, priv
from hoshino.typing import CQEvent
from .utils import *

CONFIG = load_config()
BOT = CONFIG['BOT']
ATBOT = f'[CQ:at,qq={BOT}]'
UNKNOWN = None
IDK = '我不知道'
taowa = '我俺你汝是谁爸妈爹娘父母奶姥'
qunyou = '群友'
MEMBER = os.path.expanduser('~/.Steam_watcher/member.json')

sv_help = '''
[DotA2Watcher] 群友别名设置
'''.strip()

sv = Service(
    name='WhoIs',
    use_priv=priv.NORMAL,
    manage_priv=priv.ADMIN,
    visible=True,
    enable_on_default=True,
    bundle='娱乐',
    help_=sv_help
)

DEFAULT_DATA = {}

WhoIs = None

class Whois:
    def __init__(self, **kwargs):
        if not os.path.exists(MEMBER):
            dumpjson(DEFAULT_DATA, MEMBER)

        self._rosters = {}
        self._update()

    def whois(self, group, user, obj):
        object = self.object_explainer(group, user, obj)
        name = object['name']
        uid  = object['uid']
        data = loadjson(MEMBER)
        if name == '我':
            obj = name
            uid = str(BOT)
        if name == '你':
            if random.randint(1, 10) == 1:
                return '你就是你'
            try:
                names = data[group][user]
            except:
                return '我不认识'
            return f'你是{"，".join(names)}！'
        if not obj:
            return IDK
        if uid == UNKNOWN:
            return f'{obj}？{IDK}'
        if obj == name:
            if random.randint(1, 10) == 1 or len(data[group][uid]) == 1:
                return f'{name}就是{name}'
            else:
                return f'{name}是{"，".join(data[group][uid][1:])}！'
        else:
            return f'{obj}是{data[group][uid][0]}'

    def alias_equals(self, group, user, obj1, obj2):
        data = loadjson(MEMBER)
        if not obj1 or not obj2:
            return '啥？'
        if obj1 == obj2:
            return '这不是一样嘛'
        root1 = self.object_explainer(group, user, obj1)['name']
        root2 = self.object_explainer(group, user, obj2)['name']
        if root1 == '我':
            root1 = self.object_explainer(group, user, str(BOT))['name']
        elif root1 == '你':
            root1 = self.object_explainer(group, user, user)['name']
        if root2 == '我':
            root2 = self.object_explainer(group, user, str(BOT))['name']
        elif root2 == '你':
            root2 = self.object_explainer(group, user, user)['name']
        if obj1 == '你':
            obj1 = '我'
        elif obj1 == '我':
            obj1 = '你'
        if obj2 == '你':
            obj2 = '我'
        elif obj2 == '我':
            obj2 = '你'
        if root1 and root2:
            if root1 == root2:
                return f'{obj1}是{root1}，{obj2}也是{root2}，所以{obj1}是{obj2}'
            else:
                return f'{obj1}是{root1}，{obj2}是{root2}，所以{obj1}不是{obj2}'
        else:
            return random.choice([
                IDK,
                '难说，毕竟兵不厌诈',
                '不好说，我只能说懂的都懂',
                '不知道，毕竟我只是一只小猫咪',
                'それはどうかな…',
            ])

    def add_alias(self, group, user, subject, object):
        if not object:
            return '是啥？'
        data = loadjson(MEMBER)
        sbj = self.object_explainer(group, user, subject)
        ''' 如果默认名字存在，则obj是object对应的默认名字 '''
        ''' 如果默认名字不存在，则obj是object '''
        obj = self.object_explainer(group, user, object)['name'] or object
        ''' 获取obj的owner '''
        owner = self.get_uid(group, obj)
        ''' obj已被占用，即object存在对应的默认名字，现在obj是object对应的默认名字 '''
        if owner != UNKNOWN:
            ''' 尝试将object转换成已记录的大小写形式 '''
            # 遍历群友名单中owner的所有名字
            for n in data[group][owner]:
                # 除了大小写可能不同以外完全一致
                if n.lower() == object.lower():
                    obj = n
                    break
            # owner是sbj本身
            if owner == sbj['uid']:
                return f'{sbj["name"]}已经是{obj}了'
            # owner是其他人
            return f'唔得，{data[group][owner][0]}已经是{obj}了'
        ''' obj未被占用，即object不存在对应的默认名字，现在obj是object '''
        if obj in taowa or True in [i in obj for i in taowa]:
            return '不准套娃'
        if qunyou in obj:
            return '唔得，大家都是群友'
        ''' sbj准备 '''
        if group not in data:
            data[group] = {}
        if sbj['uid'] not in data[group]:
            if sbj['uid'] == UNKNOWN:
                return f'我们群里有{subject}吗？'
            data[group][sbj['uid']] = []
        data[group][sbj['uid']].append(obj)
        with open(MEMBER, 'w', encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        self._update()
        if not sbj["name"]:
            sbj["name"] = subject
        return f'好，现在{sbj["name"]}是{object}了'

    def set_default_alias(self, group, user, name):
        if self.add_alias(group, user, '我', name) == '不准套娃':
            return '不准套娃'
        data = loadjson(MEMBER)
        data[group][user].remove(name)
        data[group][user] = [name,] + data[group][user]
        with open(MEMBER, 'w', encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        self._update()
        return f'好的，{name}'

    def del_alias(self, group, user, name):
        data = loadjson(MEMBER)
        if group not in data:
            return None
        elif user not in data[group]:
            return '你谁啊？'
        elif name in data[group][user]:
            reply = f'好，你不再是{name}了'
            data[group][user].remove(name)
            if len(data[group][user]) == 0:
                data[group].pop(user)
                reply += '\n现在群友名单里没有你了'
            with open(MEMBER, 'w', encoding='utf8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self._update()
            return reply
        else:
            return f'你本来就不是{name}'

    def del_all_alias(self, group, user):
        data = loadjson(MEMBER)
        if group not in data:
            return None
        elif user not in data[group]:
            return '你谁啊？'
        else:
            if len(data[group][user]) == 1:
                return f'唔得，你只剩下{data[group][user][0]}了'
            to_del = data[group][user][1:]
            data[group][user] = data[group][user][0:1]
            with open(MEMBER, 'w', encoding='utf8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self._update()
            return f'好，你不再是{"，".join(to_del)}了'

    def _update(self):
        data = loadjson(MEMBER)
        self._rosters = {}
        for group in data:
            self._rosters[group] = pygtrie.CharTrie()
            for user in data[group]:
                for name in data[group][user]:
                    if name.lower() not in self._rosters[group]:
                        self._rosters[group][name.lower()] = user

    def get_uid(self, group, obj):
        ''' 如果obj是at，返回obj中的uid '''
        try:
            uid = re.match('\[CQ:at,qq=(\d+)\]', obj.strip())[1]
            return uid
        except:
            pass
        ''' 如果obj本身就是uid，返回obj '''
        data = loadjson(MEMBER)
        if group in data and obj in data[group]:
            return obj
        ''' 如果obj不是at也不是uid，从群友名单中找obj对应的uid '''
        if group in self._rosters:
            if obj.lower() in self._rosters[group]:
                return self._rosters[group][obj.lower()]
        ''' 找不到，返回UNKNOWN '''
        return UNKNOWN

    def object_explainer(self, group, user, obj) -> dict:
        '''
        输入为用户视角：“我”是用户，“你”是BOT
        输出为BOT视角 ：“我”是BOT，“你”是用户
        '''
        obj = obj.strip()
        data = loadjson(MEMBER)
        if obj == '我':
            uid = user
            name = '你'
        elif obj == '你':
            uid = str(BOT)
            name = '我'
        else:
            # obj对应的uid和默认名字
            # 若不存在则为UNKNOWN
            uid = self.get_uid(group, obj)
            try:
                name = data[group][uid][0]
            except:
                name = UNKNOWN
        return {'uid': uid, 'name': name}

@nonebot.on_startup
async def whois_init():
    global WhoIs
    WhoIs = Whois()

@sv.on_fullmatch('查询群友')
async def query_group_member(bot, ev: CQEvent):
    group_id = str(ev['group_id'])
    data = loadjson(MEMBER)
    if group_id in data and len(data[group_id]):
        await bot.send(ev, '本群群友有{}'.format("，".join([data[group_id][p][0] for p in data[group_id].keys()])))
    else:
        await bot.send(ev, '没有查询到本群群友')

@sv.on_rex(r'^(.+)是不是(.+)[?？]?')
async def alias_equals(bot, ev: CQEvent):
    group_id = str(ev['group_id'])
    user_id = str(ev['user_id'])
    match_msg = ev['match']
    if match_msg.group(1) and match_msg.group(2):
        await bot.send(ev, WhoIs.alias_equals(group_id, user_id, match_msg.group(1).strip(), match_msg.group(2).strip()))

@sv.on_rex(r'^(.+)是谁[?？]?')
async def whois(bot, ev: CQEvent):
    group_id = str(ev['group_id'])
    user_id = str(ev['user_id'])
    match_msg = ev['match']
    await bot.send(ev, WhoIs.whois(group_id, user_id, match_msg.group(1).strip()))

@sv.on_rex('我不是(.+)', only_to_me=True)
async def del_alias(bot, ev: CQEvent):
    group_id = str(ev['group_id'])
    user_id = str(ev['user_id'])
    match_msg = ev['match']
    await bot.send(ev, WhoIs.del_alias(group_id, user_id, match_msg.group(1).strip()))

@sv.on_rex('([^不]+)是([^不]+)', only_to_me=True)
async def add_alias(bot, ev: CQEvent):
    group_id = str(ev['group_id'])
    user_id = str(ev['user_id'])
    match_msg = ev['match']
    try:
        await bot.send(ev, WhoIs.add_alias(group_id, user_id, match_msg.group(1).strip(), match_msg.group(2).strip()))
    except:
        await bot.send(ev, '嗯？ {}'.format(str(sys.exc_info())))  

@sv.on_rex('请叫我(.+)', only_to_me=True)
async def set_default_alias(bot, ev: CQEvent):
    group_id = str(ev['group_id'])
    user_id = str(ev['user_id'])
    match_msg = ev['match']
    await bot.send(ev, WhoIs.set_default_alias(group_id, user_id, match_msg.group(1).strip()))

@sv.on_rex(r'^我(什么|谁|啥)(也|都)不是', only_to_me=True)
async def del_all_alias(bot, ev: CQEvent):
    group_id = str(ev['group_id'])
    user_id = str(ev['user_id'])
    await bot.send(ev, WhoIs.del_all_alias(group_id, user_id))