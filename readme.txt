后台相关:
django+python

api:
包装给外部使用的接口

center:
后台管理工程

db:
数据库脚本

doc:
文档

开发环境mac
1.setup mysql server
2.sudo easy_install pip
3.sudo pip install mysqlclient

ssh 10.21.211.230
cd /home/yxgl/code/support && svn up
#update center:
python rsync_update_center.py update_all

#update api:
python rsync_update_api.py update_all

#update pay:
python rsync_update_pay.py update_all
