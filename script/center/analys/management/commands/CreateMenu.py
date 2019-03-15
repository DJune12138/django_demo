#coding=utf-8

import sys, csv, traceback
from django.core.management import BaseCommand
from models.menu import Menu

# 菜单文件每行格式：菜单序号(空格)菜单名(换行)。举例如下：
# 1 菜单1
# 1.1 菜单1.1
# 1.1.1 菜单1.1.1

# python manager.py CreateMenu e:/houtai_v2.5/menu.txt


class Command(BaseCommand):
    fixId = 0
    Menu_Map = {}
    Menu_model_map = {}

    def handle(self, *args, **options):
        fileDir = ''
        if len(args) == 0:
            sys.stdout.write('缺少参数: 请输入菜需要创建的菜单数据文件.')
            return
        else:
            fileDir = args[0]
            if not isValidFiledir(fileDir):
                sys.stdout.write('错误: 无效的文件路径.')
                return

        c = csv.reader(open(fileDir), delimiter=' ')
        for i in c:
            try:
                if not i: continue
                von = i[0].replace('\t', '').strip()
                if not von or '#' in von: continue
                selfId, parentId, order = self.getIdAndParentId(von)    #处理获得id，父id，排序
                name = i[1].replace('\t', '').strip()
                url = i[2].replace('\t', '').strip() if len(i)>=3 else ''
                menu_type = None
                if len(i)>=4:
                    menu_type = int(i[3].replace('\t', '') or 0)
                    #None 显示菜单,不记录日志; 0 不显示菜单,记录日志,1 不显示菜单,不记录日志 ,2 显示菜单,记录日志
                is_show = 1 if menu_type in (None,2) else 0
                menu,created = Menu.objects.get_or_create(name=name)
                menu.parent_id = parentId
                menu.url =  url
                menu.css = ''
                if  parentId!=0:
                    if not menu.icon and not url:
                        menu.css = menu.css or 'text-decoration: line-through'
                    parent_model = self.Menu_model_map.get(menu.parent_id,None)
                    menu.url = url or "javascript:;"
                    if parent_model:
                        parent_model.css = ''
                        parent_model.save()
                menu.is_show = is_show
                menu.is_log = menu.is_log or 1 if menu_type in (0,2) else 0
                menu.order = order
                menu.save()
                self.Menu_Map[selfId] = menu.id
                self.Menu_model_map[menu.id] = menu
                print '%s  [%s] %s done !' % (name,url,menu.css )
            
            except:
                print i
                traceback.print_exc()
        sys.stdout.write('菜单添加完成.')

    def getIdAndParentId(self,von ):
        if not '.' in von:
            selfId = von
            parentId = '0'
            self.fixId += 1
            order = self.fixId 
        else:
            von_split = von.split('.')
            selfId = ''.join(von_split)
            parentId = ''.join(von_split[:-1])
            order = von_split[-1]
            parentId = self.Menu_Map.get(parentId,parentId)
        return selfId, int(parentId), order

def isValidFiledir(fileDir):
    try:
        with open(fileDir) as f:
            return True
    except:
        return False
