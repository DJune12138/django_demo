# -*- coding:UTF-8 -*-
#线程池 by xzr

import threading
import time,datetime
import Queue

import os,sys
import traceback
import functools


def async(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        my_thread.setDaemon(True)
        my_thread.start()
    return wrapper

class ThreadWork(threading.Thread):
        def __init__(self,manager,mark):
            super(ThreadWork,self).__init__()
            self.manager = manager
            self.setDaemon(True)
            self.mark = mark

        def run(self,get_ret=True):
            while 1:
                try:
                    func_grgs = self.manager.jobQ.get()
                    if func_grgs:
                        #print '%s get the job' % self.mark
                        res = apply(*func_grgs)
                        if get_ret :
                            self.manager.resultQ.put(res)
                        self.manager.jobQ.task_done()
                    else:
                        self.manager.is_close_threads.remove(self.mark)
                        break
                except :
                    traceback.print_exc()
                    time.sleep(0.01)

class ThreadPool(object):
        def __init__(self,pool_size=100):
            self.pool_size = pool_size
            self.jobQ = Queue.Queue(0)
            self.resultQ = Queue.Queue(0)
            self.threads = []
            self.is_close_threads = []
            for i in xrange(pool_size):
                t = ThreadWork(self,i)
                self.is_close_threads.append(i)
                t.start()
                self.threads.append(t)

        def append(self,func,args=()):
            self.jobQ.put((func,args))

        def get_result(self):
                while 1:
                    try:
                        yield  self.resultQ.get_nowait()
                        if not self.is_close_threads:break
                    except Queue.Empty:
                        time.sleep(0.01)

        def get_all_result(self):
            return [ r for r in self.get_result() ]

        def close(self):
            for _ in xrange(len(self.threads)):
                self.jobQ.put(None)
        def join(self):
            for t in self.threads:
                t.join()
        def __del__(self):
            self.close()
            self.join()