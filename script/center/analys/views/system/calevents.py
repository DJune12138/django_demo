#encoding:utf-8

# =========== django import ===========
from django.shortcuts import render_to_response
from django.http import HttpResponse
# =====================================

import calendar
from django.db.models import Q
from datetime import datetime
from urls.AutoUrl import Route
from models.calevents import Calevents

@Route()
def calendar_list(request):
    the_user = request.admin
    sdate = request.POST.get("sdate")
    edate = request.POST.get("edate")
    aid = the_user.id

    nowt = datetime.now()
    if not sdate:
        sdate = "%s-%s-%s 00:00:00" % (nowt.year, nowt.month, "01")

    if not edate:
        edate = "%s-%s-%s 23:59:59" % (nowt.year, nowt.month, calendar.monthrange(nowt.year, nowt.month)[1])

    models = Calevents.objects.filter(Q(start__gte=sdate) & Q(start__lte=edate))

    for model in models:
        model.start = str(model.start)
        model.end = str(model.end)
        model.update_time = str(model.update_time)

    return render_to_response("system/calevents.html", locals())

@Route()
def calendar_save(request):
    the_user = request.admin
    event = request.GET.get("title")
    descript = request.GET.get("descript")
    start = request.GET.get("startf")
    end = request.GET.get("endf")
    all_day = request.GET.get("allDay")
    cls_name = request.GET.get("className", "")

    if not event:
        return HttpResponse('{"code":1, "msg":"事件描述不能为空!"}')

    if all_day == "true":
        end = start

    sid = 0
    try:
        calevent = Calevents(creator=the_user.username, editor=the_user.username, event=event, descript=descript, start=start,
                             end=end, all_day=1 if all_day=='true' else 0, class_name=cls_name, update_time=datetime.now())
        calevent.save()
        sid = calevent.id
    except Exception,e:
        print e
        return HttpResponse('{"code":1, "msg":"%s"}' % e)

    return HttpResponse('{"code":0, "id":%s, "creator":"%s"}' % (sid, the_user.username))

@Route()
def calendar_edit(request):
    eid = request.GET.get("eid")
    event = request.GET.get("title")
    descript = request.GET.get("descript")
    start = request.GET.get("startf")
    end = request.GET.get("endf")
    all_day = request.GET.get("allDay")
    class_name = request.GET.get("className")
    admin = request.admin.username

    calevent = None
    try:
        calevent = Calevents.objects.get(id=eid)
    except Exception,e:
        print e

    if not calevent:
        return HttpResponse('{"code":-1, "msg":"事件日志不存在!"}')

    now = str(datetime.now())[:19]

    calevent.event = event
    calevent.editor = admin
    calevent.descript = descript
    calevent.start = start
    calevent.class_name = class_name
    if end: calevent.end = end
    calevent.update_time = now
    if start: calevent.start = start
    if end: calevent.end = end
    if all_day: calevent.all_day = 1 if all_day == "true" else  0
    calevent.save()

    return HttpResponse('{"code":0, "editor":"%s", "time":"%s"}' % (admin, now))

@Route()
def calendar_delete(request):
    eid = request.GET.get("eid")

    calevent = Calevents.objects.get(id=eid)
    calevent.delete()

    return HttpResponse('{"code":0}')