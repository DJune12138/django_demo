#coding:utf-8
from django.core.management.base import BaseCommand, CommandError

import models  
from django.forms import ModelForm  

import pprint
from django.db.models.base import ModelBase
    
class Command(BaseCommand):
    help = 'all 打印模型的input html'

    def handle(self, *args, **options):
        if len(args)>=1:
            _model_name = args[0]
            if _model_name == 'all':
                print '-' * 40
                for m in dir(models):
                    _m = getattr(models,m)
                    if isinstance(_m,ModelBase):
                        print _m.__name__
            else:
                if hasattr(models,_model_name):
                    _m = getattr(models,_model_name)
                    _t = ['%4s<table>' % ' ']
                    print 
                    for f in  _m._meta.fields:
                        _t.append('%8s<tr>' % ' ')
                        _input = '<td>%s:<inout  maxlength=%s type="text" name="%s" value="{{m.%s}}"></td>' % (f.verbose_name,\
                                                                                                       f.max_length or 200,
                                                                                                       f.name,f.name)
                        _t.append('%16s%s' %(' ',_input))                                                                        
                        _t.append('%8s</tr>' % ' ' )
                    _t.append('%4s</table>' % ' ')
                    print('\n'.join(_t))
        else:
            print 'must entry model name!'

