# -*- coding: utf-8 -*-
#
# Django settings for analys project.
#

import sys
reload(sys)
sys.setdefaultencoding('utf8')   

import os
import socket
HOSTNAME = socket.gethostname()

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = '*'


EMAIL_HOST = 'smtp.qq.com'              #邮件smtp服务器
EMAIL_PORT = 25                         #端口
EMAIL_HOST_USER = '2025096180@qq.com'   #邮件账户
EMAIL_HOST_PASSWORD = 'P@ssword'        #密码
SERVER_EMAIL = '2025096180@qq.com'      #默认账户
EMAIL_USE_TLS = False                   #与SMTP服务器通信时，是否启动TLS链接(安全链接)

ADMINS = (
     ('2025096180', '2025096180@qq.com'),
)

MANAGERS = ADMINS

_op = os.path.dirname
PROJECT_ROOT = _op(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

APP_LABEL = os.path.basename(PROJECT_ROOT)
def get_app_label():
        return APP_LABEL

#账号前缀
account_prefix = 'yxgl'

#session引擎设置
#SESSION_ENGINE='django.contrib.sessions.backends.cache'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
CACHE_MIDDLEWARE_SECONDS=3600

# 上报客服问题
#外网
# QUESTION_SYNC_ADDRESS = 'http://www.gzyouai.com:8008/sync/data/question'
# 内网
QUESTION_SYNC_ADDRESS = 'http://10.19.190.18:8008/sync/data/question'
QUESTION_APP_ID = 'mhtxdl_id_kefu'
QUESTION_APP_KEY = 'mhtxdl_key_kefu'

# 支付
PAY_FUNC_URL = 'http://10.21.210.175:8888/yxgl/pay'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yx_center',
        'USER': 'root',
        'PASSWORD': 'mhtx123123',
        'HOST': '10.21.210.175',
        'PORT': '3336',
    },
    'read': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yx_center',
        'USER': 'root',
        'PASSWORD': 'mhtx123123',
        'HOST': '10.21.210.175',
        'PORT': '3336',
    },
    'write': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yx_center',
        'USER': 'root',
        'PASSWORD': 'mhtx123123',
        'HOST': '10.21.210.175',
        'PORT': '3336',
    },
    'card': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yx_card',
        'USER': 'root',
        'PASSWORD': 'mhtx123123',
        'HOST': '10.21.210.175',
        'PORT': '3336',
    },
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'cn-zh'
DEFAULT_CHARSET='utf-8'
SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(os.path.dirname(PROJECT_ROOT), 'static').replace('\\','/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = MEDIA_ROOT

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'


# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'f7r5a)rf1j99le=$jnq2rq&o1yoezuq#q9#2r)s^pz1i-6eja-'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.messages.middleware.MessageMiddleware',
    #'middleware.CustomRequestMiddleware',
    #'middleware.AuthMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)
INTERNAL_IPS = ('10.20.201.172','100.100.100.1','100.100.100.101','127.0.0.1')

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(PROJECT_ROOT), 'templates').replace('\\','/'),
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    #'/usr/lib/python2.6/site-packages/debug_toolbar/templates',
)

INSTALLED_APPS = (
 #   'django.contrib.auth',
 #   'django.contrib.contenttypes',
    'django.contrib.sessions',
 #   'django.contrib.sites',
 #   'django.contrib.messages',
  #  'django.contrib.staticfiles',
     APP_LABEL
#    'debug_toolbar',
)

DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
from util.logging_config import LOGGING

print '=' * 40,os.getpid()
print 'The system coding is %s !' % sys.getfilesystemencoding()
print 'The environment is %s !' % HOSTNAME
