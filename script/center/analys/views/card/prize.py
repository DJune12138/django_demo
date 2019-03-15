#coding=utf-8
# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response
from analys.models.card import CardPrize,CardBatch,Card
import datetime
import json
import re
import random
import sys
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)
    
def prize_list(request):
    query = ['1=1']
    name = request.GET.get('name','')
    status = int(request.GET.get('status','1'))
    query.append(' and status = %d '% status)
    page_size = 20
    page_num = int(request.GET.get('page_num', '1'))    
    if page_num < 1:
        page_num = 1 
        
    card_prize = None
    if status == 1:
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query.append(" and end_time >= '%s'"%(current_datetime))
    elif status == 0:
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query.append(" or (end_time < '%s')"%(current_datetime))
    if name != '':
        query.append(" and `name` like '%s%s%s'"%('%%',name,'%%'))
    #return HttpResponse(''.join(query))
    total_record = CardPrize.objects.using('card').extra(where=[''.join(query)]).count() 
    if total_record:   
        card_prize = CardPrize.objects.using('card').extra(where=[''.join(query)]).order_by('-id')[(page_num - 1) * page_size:page_num * page_size] 
    parg = {}
    parg["page_num"] = page_num
    parg["page_size"] = page_size
    parg["total_record"] = total_record
    parg["prize"] = card_prize
    parg['status'] = status
    parg['now'] = datetime.datetime.now()
    parg['name'] = name
    return render_to_response('card/prize_list.html', parg)

def prize_edit(request):
    model_id = request.GET.get('id', 0)
    if model_id > 0:
        model = CardPrize.objects.using('card').get(id=model_id)
    else :
        now = datetime.datetime.now()
        model = CardPrize()
        model.id = model_id
        model.start_time = now.strftime("%Y-%m-%d 00:00:00")
        model.end_time = (now + datetime.timedelta(days=90)).strftime("%Y-%m-%d 00:00:00")
        model.config = '{}'
    config = json.loads(model.config)
    if len(config) > 0:
        config = sorted(config.items(), key=lambda e:e[1]['v'], reverse=False)
    parg = {}
    parg["model"] = model
    parg["config"] = config
    parg["last_url"] = '/card/prize/?status=1'#request.META.get('HTTP_REFERER','/card/batch/?status=1')
    return render_to_response('card/prize_edit.html', parg)  

def generate_password(num_len = 0, lower_len = 0, upper_len = 0):
    num = '23456789'
    lower = 'abcdefghjkmnpqrstuvwxyz'
    upper = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
    char = ''.join([lower,upper,num])
    tmp = ''
    password = ''
    
    if num_len != 0:
        tmp += ''.join(random.sample(num,int(num_len)))

    if lower_len != 0:
        tmp += ''.join(random.sample(lower,int(lower_len)))
                
    if upper_len != 0:
        tmp += ''.join(random.sample(upper,int(upper_len)))
    
    if tmp != '':
        password = ''.join(random.sample(tmp,int(num_len) + int(lower_len) + int(upper_len)))
        
    if password == '':
        password = ''.join(random.sample(char,6))
    return password

'''
[{"id":1,"prize":"1001","v":1},{"id":1,"prize":"1002","v":5},{"id":1,"prize":"1003","v":10},{"id":1,"prize":"1004","v":12},{"id":1,"prize":"1005","v":22},{"id":1,"prize":"1006","v":50}]
{"1001":{"prize":"1001","v":1},"1002":{"prize":"1002","v":5},"1003":{"prize":"1003","v":10},"1004":{"prize":"1004","v":1000}}
'''
def prize_save(request):
    msg = ''
    print request
    model_id = request.GET.get('id','')
    model_id = int(model_id)
    name = request.POST.get('name','')
    #config = request.POST.get('config','')
    remark = request.POST.get('remark','')
    start_time = request.POST.get('start_time','')
    end_time = request.POST.get('end_time','')
    
    key_list = request.POST.getlist('key[]',[])
    v_list =  request.POST.getlist('v[]',[])
    prize_list = request.POST.getlist('prize[]',[])
    if name == '':
        msg = '名称不能为空！'
    elif start_time == '' or end_time == '':
        msg = '时间不能为空！'        
    elif start_time > end_time:
        msg = '开始时间不能大于结束时间！'
    elif end_time < datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
        msg = '结束时间不能小于服务器时间！'
    
    if model_id > 0:
        model = CardPrize.objects.using('card').get(id = model_id)
    else:
        model = CardPrize()
    config = {}
    if msg == '' and len(key_list) > 0 and name !='' and start_time != '' and end_time != '':
        try:
            for index, item in enumerate(key_list):
                key = item
                v = v_list[index]
                prize = prize_list[index]
                if not re.match('\d+$', str(key)):
                    msg = '礼包卡KEY格式有误'
                elif not re.match('[0-9]*[1-9][0-9]*$', str(v)):
                    msg = '概率值只能是正整数'
                if msg != '':
                    break;
                config[key] = {"v":v, "prize" : "%s" % prize}
        except Exception, e:
            print 'json error',e
            msg = '配置格式有误！请检查！' 
            
        if msg == '' and len(config) > 0:
            try:
                model.name = name
                model.start_time = start_time
                model.end_time = end_time
                model.config = json.dumps(config)
                model.remark = remark
                if model.code == '' or model.code == None or model.code == 'None':
                    model.code = generate_password(2, 3, 3)
                model.save(using='card')
            except Exception,e:
                print 'save card prize error',e
                msg = '%s'%e
    parg = {} 
    parg['err_msg'] = msg
    parg['next_url'] = '/card/prize/?status=1'#request.POST.get('last_url','/card/batch/?status=1')
    #return HttpResponseRedirect('/card/batch/?status=1')
    if msg:
        return render_to_response('feedback.html', parg)
    parg['msg'] = '保存成功！'
    return render_to_response('card/feedback.html', parg)

def get_rand(proArr):
    result = '' 
 
    #概率数组的总概率精度 
    proSum = 0 
    for k, v in proArr.items():
        proSum += v
    #概率数组循环 
    for k, v in proArr.items():
        randNum = random.randint(1, proSum)
        if randNum <= v:
            result = k
            break
        else:
            proSum -= v 
    proArr = None
    return result
    
def prize_del(request):
    ids = request.GET.get('ids','0')
    if ids != '':
        try:
            card_prize = CardPrize.objects.using('card').filter(id__in = ids.split(','))
            for item in card_prize:
                item.status = 0 
                item.save(using='card')
        except Exception, e:
            print('del card prize error:', e)
    else:
        return HttpResponse("id不能为空！")
    return render_to_response('feedback.html')

def prize_recover(request):
    ids = request.GET.get('ids','0')
    if ids != '0':
        try:
            card_prize = CardPrize.objects.using('card').filter(id__in = ids.split(','))
            for item in card_prize:
                item.status = 1 
                item.save(using='card')
        except Exception, e:
            print('recover card_prize error:', e)
    else:
        return HttpResponse("id不能为空！")
    return render_to_response('feedback.html')
