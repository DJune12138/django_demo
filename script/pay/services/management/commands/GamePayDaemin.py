#coding=utf-8

import sys, csv, traceback
from django.core.management import BaseCommand
from models.channel import Agent,Channel
import random


class Command(BaseCommand):
    '''充值后台进程
    '''
    def handle(self, *args, **options):
        
        agent_channels = {}
        
        



