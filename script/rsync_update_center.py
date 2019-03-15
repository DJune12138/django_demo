#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  center更新脚本
#  脚本所在的机器必须是linux 及存有私钥

import sys
import os


class RsyncTarget(object):
    ip = ''
    port = 22
    path = ''
    rsync_all_cmd = '''rsync {opts} -e 'ssh -p{port}' --include-from=rsync_include_file  --exclude-from=rsync_exclude_file --backup --backup-dir="../backup/center_`date +%Y-%m-%d_%H_%M`" ./center/  {ip}:{path}'''
    rsync_only_cmd = '''rsync {opts} -e 'ssh -p{port}' --files-from=rsync_only_files --backup --backup-dir="../backup/center_`date +%Y-%m-%d_%H_%M`" ./center/  {ip}:{path}'''
    rsync_local_cmd = '''rsync -avz --files-from=rsync_only_files --backup --backup-dir="../backup/center_`date +%Y-%m-%d_%H_%M`" ./center/  {path}'''

    @classmethod
    def exc_restart(cls):
        _cmd = 'ssh -p%s %s "cd %s;sh uwsgi_reboot.sh"' % (cls.port, cls.ip, cls.path + '/center')
        print _cmd
        return os.system(_cmd)

    @classmethod
    def get_rsync_cmd(cls, opts='-avz', all=False, local=False):
        if local:
            return cls.rsync_local_cmd.format(path=cls.path)
        if all:
            return cls.rsync_all_cmd.format(opts=opts, ip=cls.ip, path=cls.path, port=cls.port)
        else:
            return cls.rsync_only_cmd.format(opts=opts, ip=cls.ip, path=cls.path, port=cls.port)

    @classmethod
    def list(cls, all=False):
        _cmd = cls.get_rsync_cmd('-arvnz ', all=all)
        os.system(_cmd)

    @classmethod
    def exc_update(cls, *args, **kwargs):
        _cmd = cls.get_rsync_cmd(*args, **kwargs)
        print _cmd
        confirm = raw_input('确定吗？[y/s]:')
        if confirm == 'y':
            os.system(_cmd)


class inner(RsyncTarget):
    ip = '10.21.210.175'
    path = '/data/www/yxgl/center'

class test(RsyncTarget):
    ip = '129.204.149.3'
    path = '/data/www/yxgl/center'

targets = [inner, test]


def _print_targets():
    print '-' * 40
    print 'Targets:'
    for i, t in enumerate(targets):
        print ' ' * 5, '%s.' % (i + 1), t.__name__
    print '-' * 40


def main():
    _print_targets()
    print '更新全部并重启 [all]'
    update_or_restart = ''
    if len(sys.argv) >= 2:
        update_or_restart = sys.argv[1]

    choice = raw_input('输入目标:')

    if choice == 'status':
        _print_targets()
    elif choice == 'all':
        for t in targets:
            t.exc_update(all=True)

    else:
        _t = globals()[choice]
        if update_or_restart == 'update_all':
            _t.exc_update(all=True)
        elif update_or_restart == 'update_only':
            _t.exc_update(all=False)
        elif update_or_restart == 'update_local':
            _t.exc_update(local=True)
        elif update_or_restart == 'restart':
            _t.exc_restart()
        elif update_or_restart == 'list_all':
            _t.list(all=True)
        elif update_or_restart == 'list_only':
            _t.list(all=False)
        else:
            print '-' * 40
            print 'ip  :%s' % _t.ip
            print 'path:%s' % _t.path
            print 'cmd :%s' % _t.get_rsync_cmd()
            print '-' * 40
            print 'Usage python %s [update_all|list_all]' % sys.argv[0]
if __name__ == '__main__':
    main()
