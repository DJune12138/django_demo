数据库初始化:

mysqldump -h10.21.210.175 -P3336 -uroot -p'mhtx123123' -t yx_center --tables admins_new admins_new_role dict_value custom_menu def_dict def_gm def_log menu_new query_new resource role_new role_new_resource statistic_new > init.sql

mysqldump -h10.21.210.175 -P3336 -uroot -p'mhtx123123' --opt -d yx_card --set-gtid-purged=OFF > card.sql
mysqldump -h10.21.210.175 -P3336 -uroot -p'mhtx123123' --opt -d yx_center --set-gtid-purged=OFF > center.sql

log库生成方式:
http://centermhtx.ios.shyouai.com:8001/log/dbsql?server_id=2

http://150.109.106.144:8001/log/dbsql?server_id=2

更换server_id的值