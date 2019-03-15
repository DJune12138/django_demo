#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Create your views here.
import re
import os
import csv
import traceback

from django.db.models import Q
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import Context, Template

from views.base import mkdir
from models.help import Help, HelpCategory

from settings import TEMPLATE_DIRS, MEDIA_ROOT, STATIC_ROOT


TIMES = 1000


# 删除
def help_del(request, model_id=0):
    model_id = int(model_id or request.REQUEST.get('id', '0') or 0)

    if model_id:
        model = Help.objects.get(id=model_id)
        update_output_category(model.filename, model.parent_id)
        model.delete()
    return HttpResponseRedirect('/help/list/')


# 修改
def edit(request, model_id=0):
    model_id = int(model_id)
    if 0 == model_id:
        model_id = int(request.GET.get('id', 0))
    if model_id > 0:
        model = Help.objects.get(id=model_id)
    else:
        model = Help()
        model.id = model_id
        model.order = 0

    cgname = HelpCategory.objects.all()
    return render_to_response('help/edit.html', {'model': model, 'cgname': cgname})


def save(request, model_id=0):
    model_id = int(model_id)
    if 0 == model_id:
        model_id = int(request.GET.get('id', 0))
    if model_id > 0:
        model = Help.objects.get(id=model_id)
    else:
        model = Help()
    order = request.POST.get('order', 0)
    parent_id = request.POST.get('parent_id', 0)
    erro_msg = ''
    try:
        order = float(order)
        parent_id = int(parent_id)
    except:
        erro_msg = u'输入的排序格式错误'
        return HttpResponse(erro_msg)

    new_filename = request.POST.get('filename', '')
    if not new_filename.startswith('help'):
        erro_msg = u'文件名错误'
        return HttpResponse(erro_msg)

    new_category_order, new_file_order = new_filename.split('.')[:2]
    new_category_order = int(new_category_order[4:])
    new_file_order = int(new_file_order)
    new_parent_id = HelpCategory.objects.get(order=new_category_order).id

    if new_parent_id != parent_id:
        erro_msg = u'文件名与分类不一致'
        return HttpResponse(erro_msg)

    update_input = False
    if new_filename != model.filename:
        update_input = True
        update_input_category(new_filename, new_parent_id)

    old_file_name = model.filename
    old_parent_id = model.parent_id

    model.filename = new_filename
    model.order = new_category_order * TIMES + int(new_filename.split('.')[1])
    model.title = request.POST.get('title', '')
    model.parent_id = parent_id
    model.content = request.POST.get('content', '')
    model.save()
    if old_file_name and old_parent_id and update_input:    # 旧 help
        update_output_category(old_file_name, old_parent_id)

    cgname = HelpCategory.objects.all()
    return render_to_response('feedback.html', {'cgname': cgname, 'err_msg': erro_msg})


# 修改类别
def category_save(request, model_id=0):
    model_id = int(model_id)
    if 0 == model_id:
        model_id = int(request.GET.get('id', 0))
    if model_id > 0:
        model = HelpCategory.objects.get(id=model_id)
    else:
        model = HelpCategory()

    res = HelpCategory.objects.all()
    err_msg = ''
    try:
        order = int(request.POST.get('order', '0'))
    except:
        err_msg = u'排序输入格式错误'

    if '' == err_msg:
        model.order = order
        model.name = request.POST.get('name', '')
        model.save()

    return render_to_response('help/category_list.html', {'cg': res, 'err_msg': err_msg})

#
#  def help_add(request):
#    raise Exception, 123
#    if request.method == 'POST':
#        title = request.POST.get('title','')
#        filename = request.POST.get('filename','')
#        parent_id = request.POST.get('parent_id',0)
#        content = request.POST.get('content','')
#        p = Help(title=title,filename=filename,parent_id=parent_id,content=content)
#        p.save()
#        return HttpResponseRedirect('/add/')
#    else:
#        category_list = HelpCategory.objects.all()
#        return render_to_response('help/add.html',{'cgname':category_list})


# 分类 管理列表
def category_list(request):
    #  if request.method == 'POST':
        #  name = request.POST.get('name','')
        #  content = HelpCategory(name=name)
        #  content.save()
        #  return HttpResponseRedirect('/help/category/categorylist/')
    #  else:
    if True:
        title = '分类列表'
        res = HelpCategory.objects.all()
        return render_to_response('help/category_list.html', {'cg': res, 'title': title})


def category_del(request, model_id=0):
    model_id = int(model_id)
    if 0 == model_id:
        model_id = int(request.GET.get('id', 0))
    p = HelpCategory.objects.get(id=model_id)
    p.delete()
    return HttpResponseRedirect('/help/category/list/')


def view(request, file_name=''):
    if file_name == '':
        file_name = request.GET.get('filename', '')

    if file_name == '' or file_name == 'index.html':
        data_list = []
        cg = HelpCategory.objects.all()
        for item in cg:
            category = {}
            helps = Help.objects.filter(parent_id=item.id)
            category['name'] = item.name
            category['helps'] = helps
            data_list.append(category)
        return render_to_response('help/index.html', {'data_list': data_list})
    else:
        file_name = file_name[:-5]
        result = Help.objects.get(filename=file_name)

        result.content = filter_content(result.content)
        return render_to_response('help/content.html',
                                  {'title': result.title, 'content': result.content})


def help_list(request):
    search_con = request.POST.get('title', '')
    parent_id = int(request.POST.get('parent_id', 0))
    if search_con == '' and parent_id == 0:
        res = Help.objects.all().order_by('parent_id', 'order')
    else:
        query = Q()
        if search_con != '':
            query = query & (Q(title__contains=search_con) | Q(content__contains=search_con))

        if 0 != parent_id:
            query = query & Q(parent_id=parent_id)
        res = Help.objects.filter(query)
    cgname = HelpCategory.objects.all()
    cgname_map = {}
    for c in cgname:
        cgname_map[c.id] = c
    for r in res:
        parent_obj = cgname_map.get(r.parent_id, None)
        if parent_obj:
            r.get_parent_id_name = parent_obj.name
    return render_to_response(
        'help/list.html', {
            'res': res, 
            'cgname': cgname, 
            'search_con': search_con,
            'parent_id': parent_id,
            'request': request
            }
        )



# 生成静态页面
def file_create(request, help_id=0):

    help_id = int(help_id)

    if 0 == help_id:
        help_id = int(request.GET.get('id', 0))

    if help_id > 0:
        res = Help.objects.filter(id=help_id)
    else:
        res = Help.objects.all()

    file_tpl = open(r'%s/help/content.html' % TEMPLATE_DIRS[0], 'r')
    tpl_content = file_tpl.read()
    file_tpl.close()
    t = Template(tpl_content)

    save_path = r'%s/help' % MEDIA_ROOT

    mkdir(save_path)
    for item in res:
        sign = '%s' % item.filename
        title = item.title
        content = filter_content(item.content)
        static_file_path = r'%s/%s.html' % (save_path, sign)
        delete_file(static_file_path)
        fileHandle = open(static_file_path, 'w')
        c = Context({"title": title, "content": content})
        c = t.render(c)
        fileHandle.write(c.encode('utf-8'))
        fileHandle.close()
    cgname = HelpCategory.objects.all()

    if help_id == 0:
        file_tpl = open(r'%s/help/index.html' % TEMPLATE_DIRS[0], 'r')
        tpl_content = file_tpl.read()
        file_tpl.close()
        t = Template(tpl_content)
        data_list = []
        cg = HelpCategory.objects.all()
        for item in cg:
            category = {}
            helps = Help.objects.filter(parent_id=item.id)
            category['name'] = item.name
            category['order'] = item.order
            category['helps'] = helps
            data_list.append(category)

        index_html_path = r'%s/index.html' % (MEDIA_ROOT + '/help')
        delete_file(index_html_path)
        fileHandle = open(index_html_path, 'w')
        c = Context({"data_list": data_list})
        c = t.render(c)
        fileHandle.write((c).encode('utf-8'))
        fileHandle.close()

    return render_to_response('help/list.html', {'res': res, 'cgname': cgname})


def filter_content(html):
    html = re.sub('\s{2,}', '\n', html)
    html = '<li>%s</li>' % ('</li><li>'.join(html.split('\n')))
    html = html.replace('<li></li>', '')
    return html


def delete_file(file_path):
    if os.path.isfile(file_path):
        #  print 'delete:', file_path
        os.remove(file_path)


def import_html_data_old(request):
    clear_db()
    fileHandle = open(r'%s/help/index.html' % (STATIC_ROOT), 'r')
    index_content = fileHandle.read()
    fileHandle.close()

    regex = ur"<li[\s]*>([\s\S]+?)</li>"
    #  regex_span = ur"<span><b>\+</b>([\S\s]+?)</span>"
    regex_span = ur"<span[\s\S]+?><img.*/>([\S\s]+?)</span>"
    regex_href = ur"href=\"(.*)\" target=\"right\""
    regex_title = ur"target=\"right\">([\S\s]+?)</a>"
    regex_body = ur"<body[\s\S]+?>([\s\S]+?)</body>"

    filter_regex = ur"<[\s\S]+?>"

    match = re.findall(regex, index_content)

    if match:
        index = 1
        order_num = 0
        for result in match:

            mark_span = re.findall(regex_span, result)
            category = HelpCategory()
            category.id = index
            category.order = index

            category.name = mark_span[0].replace(" ", "")

            category.save()

            mark_href = re.findall(regex_href, result)
            href_title = re.findall(regex_title, result)
            #  for i in range(mark_href.__len__()):
                 #  print mark_href[i]
            h_index = 0
            print category.name
            for href in mark_href:
                fileHandle_href = open(r'%s/help/%s' % (STATIC_ROOT, href), 'r')
                fileHandle_href_content = fileHandle_href.read()
                fileHandle_href.close()

                model = Help()
                model.parent_id = index
                model.order = order_num
                model.filename = href[:-5]
                model.title = href_title[h_index]

                print '-' * 40, h_index
                print model.title

                content = re.findall(regex_body, fileHandle_href_content)[0]
                content = re.sub(r'</[\s\S]+?>', '\n', content)
                content = re.sub(filter_regex, '', content)

                model.content = content
                model.save()
                order_num += 1
                h_index = h_index + 1
            index = index + 1
        return render_to_response('feedback.html')
    else:
        return render_to_response('help/help_list.html')


def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        #  print '==> row: ', row
        try:
            yield [unicode(cell, 'utf-8') for cell in row]
        except UnicodeDecodeError:
            yield [cell.decode('gbk') for cell in row]


# import csv data
def import_html_data(request):
    clear_db()
    file_name_list = ['help.csv', 'help.xlsx']

    for filename in file_name_list:
        file_path = os.path.join(STATIC_ROOT, 'help', filename)
        if os.path.exists(file_path) and filename.endswith('.csv'):
            print '==> import csv'
            try:
                csvfile = file(file_path, 'rb')
                #  reader = csv.reader(csvfile)
                reader = unicode_csv_reader(csvfile)
                for line in reader:
                    if line[0] == '0':
                        category = HelpCategory()
                        category.id = line[1]
                        category.order = line[2]
                        category.name = line[3]
                        category.save()
                    else:
                        help = Help()
                        help.id = line[1]
                        help.parent_id = line[2]
                        help.order = line[3]
                        help.filename = line[4]
                        help.title = line[5]
                        help.content = line[6]
                        help.save()
                return render_to_response('help/list.html')
            except Exception, e:
                msg = str(e)
                traceback.print_exc()
            finally:
                csvfile.close()
                return render_to_response('feedback.html')
        elif os.path.exists(file_path) and filename.endswith('.xlsx'):
            print '==> import excel'
            try:
                import_xlsx_data(file_path)
            except:
                traceback.print_exc()
            return render_to_response('feedback.html')
    else:
        return render_to_response('feedback.html')


def create_help(help_model):
    Help.objects.get_or_create(
        parent_id = help_model['parent_id'],
        order     = help_model['order'],
        filename  = help_model['filename'],
        title     = help_model['help_title'],
        content   = help_model['help_content']
    )


def import_xlsx_data(file_path):
    try:
        import xlrd
    except:
        return

    clear_db()
    table = xlrd.open_workbook(file_path).sheets()[0]

    help_model = {}
    row_key = ['category_order', 'category_title', 'help_order', 'help_title', 'help_content']
    for i in range(1, table.nrows):
        row = dict(zip(row_key, table.row_values(i)))
        # category
        if isinstance(row.get('category_order'), float) and len(row.get('category_title')):
            if help_model and help_model.get('help_content'):
                create_help(help_model)

            category_order   = int(row.get('category_order'))
            help_category, _ = HelpCategory.objects.get_or_create(
                order=category_order,
                name=row.get('category_title')
            )
            help_model                   = {}
            help_model['category_order'] = category_order
            help_model['parent_id']      = help_category.id

        # help
        if isinstance(row.get('help_order'), float) and len(row.get('help_title')):
            if help_model and help_model.get('help_content'):
                create_help(help_model)

            help_order                 = int(row.get('help_order'))
            help_model['order']        = help_model.get('category_order') * 1000 + help_order
            help_model['filename']     = "help%s" % (str(help_model['category_order']) + '.' + str(help_order))

            help_model['help_title']   = row.get('help_title')
            help_model['help_content'] = row.get('help_content')
        elif not row.get('help_order') and not row.get('help_title') and row.get('help_content'):
            help_model['help_content'] += '\n'
            help_model['help_content'] += row.get('help_content')
    else:
        if help_model and help_model.get('help_content'):
            create_help(help_model)


def clear_db():
    HelpCategory.objects.all().delete()
    Help.objects.all().delete()



def help_export(request):
    '''帮助导出
    '''
    ##  the_static_help_dir = os.path.join(STATIC_ROOT, 'help')
    #  tmp_pwd = os.getcwd()
    #  the_static_help_file = os.path.join(STATIC_ROOT, 'help.tar.gz')
    #  if os.path.isfile(the_static_help_file):
        #  os.remove(the_static_help_file)
    #  os.chdir(STATIC_ROOT)
    #  tar_cmd = 'tar zcf help.tar.gz help/'
    #  os.system(tar_cmd)
    #  os.chdir(tmp_pwd)
    #  return HttpResponseRedirect('/static/help.tar.gz')

    # 原处理方式，用tar打包成tar.gz文件打包导出，编辑完成后再用zip压缩导入
    # 新处理方式，以csv导出，编辑完成后导入
    file_name = 'help.csv'
    file_path = os.path.join(STATIC_ROOT, file_name)
    if os.path.isfile(file_path):
        os.remove(file_path)

    csvfile = file(file_path, 'wb')
    writer = csv.writer(csvfile)
    data = []

    # 帮助目录
    category_type = 0
    all_category = HelpCategory.objects.all()
    category_data = []
    for i in all_category:
        category_data.append((category_type, i.id, i.order, i.name))
    data.extend(category_data)

    # 帮助内容
    help_type = 1
    all_help = Help.objects.all()
    help_data = []
    for i in all_help:
        help_data.append((help_type, i.id, i.parent_id, i.order, i.filename, i.title, i.content))
    data.extend(help_data)

    writer.writerows(data)
    csvfile.close()

    return HttpResponseRedirect('/static/' + file_name)


def help_upload(request):
    '''上传帮助压缩文件
    '''
    file_name_list = ['help.csv', 'help.xlsx']
    from util.zip import unzip_file
    msg = '没有文件!'
    file_obj = request.FILES.get('fileToUpload', None)
    if file_obj:
        the_file_name = file_obj.name
        #  if not the_file_name.endswith('.zip'):
            #  msg = '不是zip文件'
        if not the_file_name.endswith('.csv') and not the_file_name.endswith('.xlsx'):
            msg = '不是CSV/Excel文件'
        else:
            for filename in file_name_list:
                try:
                    file_path = os.path.join(STATIC_ROOT, 'help', filename)
                    os.remove(file_path)
                except OSError:
                    pass

            save_file_path = os.path.join(STATIC_ROOT, 'help', 'help.csv')
            if the_file_name.endswith('.xlsx'):
                save_file_path = os.path.join(STATIC_ROOT, 'help', 'help.xlsx')
            #  help_dir_path = os.path.join(STATIC_ROOT, 'help')

            fp = open(save_file_path, 'wb')
            try:
                for chunk in file_obj.chunks():
                    fp.write(chunk)
                fp.close()
                #  unzip_file(save_file_path, help_dir_path)
                msg = '上传成功,请点击导入文件!'
            except Exception, e:
                msg = str(e)
                traceback.print_exc()
            finally:
                fp.close()
    return HttpResponse(msg)


def update_output_category(old_file_name, old_parent_id):
    old_category_order, old_file_order = old_file_name.split('.')[:2]
    old_category_order = int(old_category_order[4:])
    old_file_order = int(old_file_order)

    output_help_list = Help.objects.filter(parent_id=old_parent_id)
    for he in output_help_list:
        file_order = int(he.filename.split('.')[1])
        if file_order > old_file_order:
            he.filename = "help" + str(old_category_order) + '.' + str(file_order - 1)
            he.order = old_category_order * TIMES + file_order - 1
            he.save()


def update_input_category(new_file_name, new_parent_id):
    new_category_order, new_file_order = new_file_name.split('.')[:2]
    new_category_order = int(new_category_order[4:])
    new_file_order = int(new_file_order)

    input_help_list = Help.objects.filter(parent_id=new_parent_id)
    for he in input_help_list:
        file_order = int(he.filename.split('.')[1])
        if file_order >= new_file_order:
            he.filename = "help" + str(new_category_order) + '.' + str(file_order + 1)
            he.order = new_category_order * TIMES + file_order + 1
            he.save()
