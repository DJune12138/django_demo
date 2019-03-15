#coding=utf-8
#转换平台

import sys, csv, traceback
from django.core.management import BaseCommand
from models.channel import Agent,Channel
import random


class Command(BaseCommand):
    '''增加平台
    '''
    def handle(self, *args, **options):
        
        agent_channels = {}
        
        for c in Channel.objects.all():
            c.agent_name = c.agent_name.strip()
            agent_name = c.agent_name.strip() or '未分平台'
            agent_channels.setdefault(agent_name,[])
            agent_channels[agent_name].append(c)
        
        for agent_name,channels in agent_channels.iteritems():
            agent_model,created = Agent.objects.get_or_create(name=agent_name)
            if created:
                agent_model.alias = agent_model.alias or agent_name
                agent_model.name = agent_model.name or agent_name
                first_channel = channels[0]
                agent_model.usermae = agent_model.name or first_channel.username
                agent_model.password = agent_model.password or first_channel.password
                agent_model.channel.clear()
                agent_model.channel.add(*channels)
                agent_model.save()
                print '增加平台:%s' % agent_name



