# -*- coding: utf-8 -*-
#自动查找url

from django.conf.urls import patterns, include, url
from django.utils.importlib import import_module
from django.core.urlresolvers import get_mod_func
from django.http import HttpResponse
from django.core.urlresolvers import reverse  


from util import trace_msg
from  settings import PROJECT_ROOT
import os,sys
import traceback

VIEWS_DIR = 'views'
Handlers = set()


class Route(object):
    '''
    @自动添加django URL
    '''
    
    def __init__(self,re_url='',name=None,*args,**kwargs):
        self.re_url = re_url
        self.args = args
        self.kwargs = kwargs
        self.name = name
        
    def __call__(self,obj):
        _m = obj.__module__
        p_m_f = '%s.%s' % (_m,obj.__name__)
        name = p_m_f.lstrip(VIEWS_DIR).strip('.')
        name = '.'.join(name.split('.')[-3:])
        uri =  name.replace('.','/')
        _doc = obj.__doc__
        
        if self.re_url == '':
            self.re_url = '^%s' % uri
            
        if hasattr(obj,'as_view'):                               #django视图类
            re_path_str = '(?P<path>\w+)'
            if re_path_str not in self.re_url:
                self.re_url = '%s/%s' % (self.re_url,re_path_str)
            setattr(obj,'url_prefix','/%s' % '/'.join(self.re_url.strip('^').split('/')[:-1]))
            obj = apply(obj.as_view)
            
        end_re_uri_str = '[/]?$'
        if end_re_uri_str not in self.re_url:
            self.re_url = '%s%s' % (self.re_url,end_re_uri_str)
        
        _url = url(self.re_url,obj,
                            name = self.name or p_m_f,
                            *self.args,**self.kwargs)
        _url.__doc__ = _doc
        setattr(_url,'doc',str(_doc).split('\n')[0])
        setattr(_url,'group',_m)
        setattr(_url,'url',self.re_url)
        Handlers.add(_url)
        return obj

def _get_pyfile(dirlist):
    dirlist = [dirlist] if isinstance(dirlist,basestring) else dirlist
    for dir in dirlist:
        if os.path.isdir(dir):
            for dirpath, dirs, files in os.walk(dir):
                for filename in files:
                    if  filename.endswith('.py'):
                        yield os.path.join(dirpath,filename)




def _import_module_from_file():
    for pyfile in _get_pyfile(os.path.join(PROJECT_ROOT,VIEWS_DIR)):
        _p_m = pyfile.replace(PROJECT_ROOT,'',1).replace('__init__','').rstrip('py').replace(os.sep,'.').strip('.')
        try:
            __import__(_p_m)
        except Exception,e:
            print trace_msg()

def reverse_view(view_or_name,*args,**kwargs):
    try:
        return reverse(view_or_name,*args,**kwargs)
    except:
        traceback.print_exc()
        return ''

def get_handlers():
    _import_module_from_file()
    return list(Handlers)








