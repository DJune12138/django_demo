#! /usr/bin/python
# -*- coding: utf-8 -*-
from models.admin import Admin
def check_author(request):
    tmp_admin = get_form_admin(request)
    
    if tmp_admin.username == '' or tmp_admin.password == '':
        return False
    
    if Admin.objects.filter(username=tmp_admin.username).count() == 0:
        return False
    
    admin = Admin.objects.filter(username=tmp_admin.username).all()[0]
    if admin.password != tmp_admin.md5_password():
        return False
    
    return True

#从表单拿取Admin 对象
def get_form_admin(request):
    user_name = request.POST.get('user_name', '')
    password = request.POST.get('password', '')
    tmp_admin = Admin();
    tmp_admin.username = user_name
    tmp_admin.password = password
    return tmp_admin