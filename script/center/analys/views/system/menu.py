# -*- coding: utf-8 -*-
# 
#菜单相关
#
#=========================================
from django.core.urlresolvers import reverse  
from django.db import connection,connections
from django.utils.html import conditional_escape 
from django.http import HttpResponse
from django.shortcuts import redirect,render_to_response,HttpResponseRedirect
from django.views.generic import ListView,View
from django.core.urlresolvers import reverse  

from django.db.models import Q
#==========================================


from models.admin import Admin, Menu
from urls.AutoUrl import Route,reverse_view
from views.base import notauth
from models.menu import UserDefinedMenu
from util import trace_msg
            
class MenuTree(object):
    def __init__(self,menu_objs):
        self.tree_node_map = {}
        self.parent_list = []
        for m in menu_objs:
            m.tt_ids = []
            m.tt_parent_ids = []
            self.tree_node_map[m.id] = m
            if m.parent_id == 0:
                self.parent_list.append(m)
        self.list_record = []
        
    def set_tt_ids(self,parent):
        child_num = 0
        for v in self.tree_node_map.values():
                if parent.id ==  v.parent_id:
                    child_num += 1
                    v.tt_ids += parent.tt_ids+[child_num]
                    v.tt_parent_ids = parent.tt_ids
                    self.list_record.append(v)
                    self.set_tt_ids(v)
    
    def get_list_record(self):
        parent_num = 0
        for parent in self.parent_list:
            parent_num +=1
            parent.tt_ids.append(parent_num)
            self.list_record.append(parent)
            self.set_tt_ids(parent)
        for m in self.list_record:
            m.tt_id = '-'.join([str(i) for i in m.tt_ids])
            m.tt_parent_id = '-'.join([str(i) for i in m.tt_parent_ids])
        return self.list_record
    

@Route()
def menu_list(request,is_menu=1):
    '''菜单列表
    '''
    parent_id = int(request.GET.get('parent_id','0'))
    #if parent_id:
    #    parent_menu = request.admin.get_resource('menu').get(id=parent_id)
    list_record = []
    menus = request.admin.get_resource('menu').all().order_by('parent_id')
    menu_tree = MenuTree(menus)
    list_record = menu_tree.get_list_record()

    return render_to_response('system/menu_list.html', locals())

@Route()
def permission_list(request):
    return menu_list(request,0)


@Route()
def menu_edit(request, id=0, parent_id=0):
    '''菜单编辑
    '''
    try:
        id = int(request.REQUEST.get('id', '0'))
        parent_id = int(request.REQUEST.get('parent_id', '0'))
        if id:
            menu = request.admin.get_resource('menu').using('write').get(id=id)
        else:
            menu = Menu()
            menu.id = id
            menu.parent_id = parent_id
            menu.url = request.GET.get('url','')
            menu.name = request.GET.get('name','')
        list_menu = Menu.objects.using('read').filter(id=menu.parent_id)
    except Exception,e:
        err_msg = trace_msg()
    return render_to_response('system/menu_edit.html', locals())


@Route()
def menu_save(request):
    '''菜单/权限保存
    '''
    try:
        id = int(request.REQUEST.get('id', '0'))
        menu = request.admin.get_resource('menu').using('write').get(id=id) if id else Menu.objects.using('write').create()
        menu.set_attr('name', request.REQUEST.get('name'),null=False)
        menu.parent_id = int(request.REQUEST.get('parent_id', '0'))
        menu.order = int(request.REQUEST.get('order', '0'))
        menu.is_show = int(request.REQUEST.get('is_show', '0'))
        menu.is_log = int(request.REQUEST.get('is_log', '0'))
        menu.set_attr('url', request.REQUEST.get('url'),null=True)
        menu.icon = request.REQUEST.get('icon', '')
        menu.css = request.REQUEST.get('css', '')
        menu.save(using='write')
    except Exception,e:
        err_msg = trace_msg()
        print err_msg
    return render_to_response('feedback.html',locals())


@Route()
def menu_remove(request, id=0):
    '''删除菜单
    '''
    err_msg = ''
    try:
        menu_ids = request.REQUEST.getlist('id')
        if menu_ids:
            for mid in menu_ids:
                Menu.objects.filter(Q(parent_id=mid)|Q(id=mid)).delete()
    except Exception,e:
        err_msg = trace_msg()
    return render_to_response('feedback.html')


@Route()
def user_menu_list(request):
    ''' 用户自定义菜单 '''
    the_user = request.admin

    menus = the_user.get_resource('menu').exclude(name="必须权限").filter(is_show=1).order_by("parent_id")
    menu_tree = MenuTree(menus)
    list_record = menu_tree.get_list_record()

    user_menus = UserDefinedMenu.objects.filter(admin_id=the_user.id)
    if user_menus:
        choice_menus = user_menus[0].defined_menu
    else:
        choice_menus = ""

    return render_to_response('system/defined_menu.html', locals())

@Route()
def user_menu_save(request):
    ''' 用户自定义菜单保存 '''
    from datetime import datetime
    def_menus = request.GET.get("d", None)
    sys_menus = request.GET.get("s", None)

    menu_owner = UserDefinedMenu.objects.filter(admin_id=request.admin.id)
    if menu_owner:
        menu_owner = menu_owner[0]
        menu_owner.defined_menu = def_menus
        menu_owner.map_menu = sys_menus
        menu_owner.update_time = datetime.now()
        menu_owner.save()
    else:
        menu_owner = UserDefinedMenu(
            admin_id=request.admin.id,
            defined_menu=def_menus,
            map_menu=sys_menus,
            update_time=datetime.now()
        )
        menu_owner.save()

    return HttpResponse("1")

@Route()
def user_menu_structure(request):
    ''' 组装自定义菜单的菜单树结构 '''
    import json
    the_user = request.admin
    user_menus = UserDefinedMenu.objects.filter(admin_id=the_user.id)

    if not user_menus:
        return HttpResponse('{"code":1}')

    dm = json.loads(user_menus[0].defined_menu)
    mm = json.loads(user_menus[0].map_menu)

    map_menus = None
    if mm:
        map_menus = Menu.objects.filter(id__in=mm.keys()).order_by("id")

    menu_structure = []
    if map_menus:
        for k,v in dm.items():
            menu_structure.append({
                "id" : str(k),
                "parent_id" : str(v[0]),
                "name" : v[1],
                "url" : "",
                "icon" : "",
                "css" : "",
            })

        for i in map_menus:
            pid = mm[str(i.id)]
            menu_structure.append({
                "id" : i.id,
                "parent_id" : pid,
                "name" : i.name,
                "url" : i.url,
                "icon" : i.icon,
                "css" : i.css
            })

    menu_tree_list = []
    def menu_tree(parent_id):
        parent_id = int(parent_id)
        for m in menu_structure:
            if int(m["parent_id"]) == parent_id:
                menu_tree_list.append(m)
                menu_tree(m["id"])
    menu_tree(0)

    return HttpResponse('{"code":0, "data":%s}' % json.dumps(menu_tree_list))