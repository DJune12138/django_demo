# -*- coding: utf-8 -*-
from settings import get_app_label

if get_app_label() != 'card':
    from admin import *
    from center import *
    from log import *
    from server import *
    from channel import *
    from statistic import *
    from gm import *
    from pay import PayChannel
    from game import *
    from query import *
    from calevents import Calevents
    #from player_template import PlayerTemplate
    from platform import PlatForm
else:
    from card import *
