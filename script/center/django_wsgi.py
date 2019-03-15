import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"analys")))

#print(os.path.abspath(os.path.dirname(__file__)))

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi

#from analys.login_service import *
#from analys.pay_service import *
#start_login_server()
#start_pay_server()

application = django.core.handlers.wsgi.WSGIHandler()
