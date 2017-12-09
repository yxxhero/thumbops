#!/usr/bin/env python2.7
#coding:utf-8
from py_daemon import py_daemon  
from wbclicklikemobile import wb_main
import redis
import logging
import sys
import signal
from setproctitle import setproctitle,getproctitle
setproctitle("taskhandle")



def exit(signum,frame):    
    print "退出程序..."
    sys.exit(1)
signal.signal(signal.SIGINT, exit)  
signal.signal(signal.SIGTERM, exit) 

#初始化日志实例
logging.basicConfig(level="DEBUG",
                format='%(asctime)s  %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                filename='./log/debug.log',
                filemode='a')

#设置全局变量
redis_addr='127.0.0.1'
redis_port=6379
redis_db=0
redis_queue="taskqueue"

#初始化redis连接池,为读取任务队列做准备
try:
    redis_pool=redis.ConnectionPool(host=redis_addr,port=redis_port,db=redis_db)
except Exception as e:
    logging.error(str(e))
else:
    logging.info("redis连接成功...")

def handletask():
    rins=redis.StrictRedis(connection_pool=redis_pool)
    while True:  
        taskinfo = rins.brpop(redis_queue, 0)  
        logging.info("taskid: "+taskinfo[1])
        try:
            processesnum,mid,upnum,rediskey=taskinfo[1].split("^")
            wb_main(processesnum,mid,upnum,rins,rediskey)
        except Exception as e:
            logging.info(str(e))
        else:
            logging.info("开始处理...")


class pantalaimon(py_daemon.Daemon):
    def run(self):
        handletask()        
        
if __name__ == "__main__":
    pineMarten = pantalaimon('/var/run/handle_task.pid')
    if len(sys.argv)==2:
        if sys.argv[1]=="start":
            pineMarten.start()
        elif sys.argv[1] =="stop":
            pineMarten.stop()
        elif sys.argv[1]=="restart":
            pineMarten.restart()
        elif sys.argv[1]=="run":
            pineMarten.run()
        else:
            print "Usage: "+sys.argv[0]+" start|restart|run|stop" 
    else:
        print "Usage: "+sys.argv[0]+" start|restart|run|stop" 
