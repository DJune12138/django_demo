#!/usr/bin/env python
# coding=utf-8
# 启动后台服务器的守护进程


import os
import sys
import time

PWD = os.path.dirname(os.path.abspath(__file__))

SERVICE_MAP = {
    "changeserver": {"cmd": "python -u center/manage.py ChangeSer", "remark": "到开服时间自动改状态"},
    "activity": {"cmd": "python -u center/manage.py AutoActivity", "remark": "自动开启活动服务"},
    "yab": {"cmd": "python -u center/analys/scripts/backup_youai/backup_youai.py -c", "remark": "游爱备份"},
    "statistic": {"cmd": "python -u center/manage.py StatisticCron -c", "remark": "统计后台服务"},
    "online": {"cmd": "python -u center/manage.py GameOnlineCron -c", "remark": "全服在线进程"},
    "notice": {"cmd": "python -u center/manage.py AutoNotice -c", "remark": "公告守护服务"},
    "card": {"cmd": "python -u api/manage.py CardDaemon", "remark": "礼包卡发放后台"},
    "repairpay": {"cmd": " python -u pay/manage.py GamePayRepairDaemon", "remark": "充值补单进程"},
    "analys": {"cmd": "sh center/uwsgi_reboot.sh", "remark": "中央后台uwsgi", "nohup": False,
               "pid_str": "center/uwsgi.xml"},
    "api": {"cmd": "sh api/uwsgi_reboot.sh", "remark": "中央礼包卡uwsgi", "nohup": False, "pid_str": "api/uwsgi.xml"},
    "pay": {"cmd": "sh pay/uwsgi_reboot.sh", "remark": "中央游戏充值服务uwsgi", "nohup": False, "pid_str": "pay/uwsgi.xml"},
    "clearlog": {"cmd": "python -u center/manage.py ClearLog", "remark": "清除掉数据量大且无用的数据"},
    "battlelist": {"cmd": "python -u center/manage.py BattleList", "remark": "跨服数据添加和积分统计"},
    # "autobanip":{"cmd":"python -u center/manage.py AutoBanIP","remark":"自动封禁IP脚本"},
    "autoserver": {"cmd": "python -u center/manage.py AutoServer", "remark": "综合排行榜"},
    # "fixpay":{"cmd":"python -u pay/manage.py fix_pay","remark":"充值渠道订单修正"},
    "channelvalue": {"cmd": "python -u center/manage.py ChannelValue", "remark": "渠道价值自动统计"},
    "automail": {"cmd": "python -u center/manage.py AutoMail", "remark": "定时邮件自动审核"},
}

ACTION_LIST = ('stop', 'start', 'status', 'list', 'restart')


class DaemonService(object):

    def __init__(self, service_name):
        self.service_name = service_name
        self.service = SERVICE_MAP.get(service_name)

    def get_service_cmd(self):
        return self.service.get('cmd').strip()

    def get_service_pid(self):
        cmd = 'pgrep -f "%s"' % (self.service.get('pid_str', '') or self.get_service_cmd())
        return self.run_cmd(cmd)

    def check_runing_status(self):
        pids = self.get_service_pid()
        servce_status_str = '%s:[%s](%s) ' % (self.service_name, self.get_service_cmd(), self.service.get('remark', ''))
        if not pids:
            print '\033[31m%s not running!\033[0m' % servce_status_str
        else:
            print '\033[32m%s running(%s)!\033[0m' % (servce_status_str, pids.replace('\n', ','))
        return pids

    def service_status(self):
        return self.check_runing_status()

    def service_start(self):
        if not self.check_runing_status():
            is_nohup = self.service.get('nohup', True)
            cmd = self.get_service_cmd()
            if is_nohup:
                log_file_name = 'log/%s_daemon.log' % self.service_name
                cmd = 'nohup %s >> %s 2>&1 &' % (cmd, log_file_name)
            self.run_cmd(cmd)
            time.sleep(1)
            return self.check_runing_status()

    def service_stop(self):
        pids = self.check_runing_status()
        if pids:
            for pid in pids.split('\n'):
                self.run_cmd('kill -9 %s' % pid)
            time.sleep(1)
            return self.check_runing_status()

    def service_restart(self):
        self.service_stop()
        self.service_start()

    def service_list(self):
        print '%s[%s] #%s' % (self.service_name, self.service.get('cmd'), self.service.get('remark'))

    def run_cmd(self, cmd_str):
        _r = os.popen(cmd_str)
        return _r.read().strip()

    def __call__(self, action_name):
        action_method = getattr(self, 'service_%s' % action_name, None)
        if not action_method:
            self.__class__.print_help()
        else:
            return action_method()

    @staticmethod
    def print_help():
        print 'Usage: %s [%s] service_name' % (__file__,
                                               '|'.join(ACTION_LIST)
                                               )


def read_parmas():
    argv = sys.argv
    if len(argv) >= 2:
        action = argv[1]
        if action in ACTION_LIST:
            if len(argv) >= 3:
                service_name = argv[2] if len(argv) >= 3 else ''
                if service_name in SERVICE_MAP:
                    daemon_service = DaemonService(service_name)
                    daemon_service(action)
                    return
                else:
                    action = 'list'

            for service_name in SERVICE_MAP:
                daemon_service = DaemonService(service_name)
                daemon_service(action)
        else:
            DaemonService.print_help()

    else:
        DaemonService.print_help()


if __name__ == '__main__':
    os.chdir(PWD)
    read_parmas()
