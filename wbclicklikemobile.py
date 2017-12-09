#!/usr/bin/python2.7
#coding=utf8


import sys
import time
import argparse

import util
from sina.wb_clicklike_mb import WbLike 

sys.path.append("../")
from module import mylog as log
from module.redis_helper import RedisHelper
from module.disperse_redis import Distributed
import multiprocessing as mp


def is_hit_black(rd, black_set, uid):
    if rd.sismember(black_set, uid):
        log.DEBUG('Hit Black[%d]' % int(uid))
        return True
    else:
        return False


def is_hit_sender_history(rd, sender_history, uid):
    if rd.sismember(sender_history, uid):
        log.DEBUG('Hit History[%d]' % uid)
        return True
    else:
        return False


def set_sender_history(rd, sender_history, uid):
    rd.sadd(sender_history, uid)


def is_timeout(timestamp, timeout):
    return (int(time.time()) - timestamp) > timeout


def get_vaild_sender(dr, rd_black, rd_black_s, rd_history, rd_history_s, timestart):
    while True:
        user = dr.get_data()
        if user['user_agent'].find('iPhone') != -1:
            continue
        
        if not is_timeout(user['cap_time'], timestart):
            log.DEBUG('user too new.')
            continue

        uid = user['uid']
        if is_hit_black(rd_black, rd_black_s, uid):
            continue

        if is_hit_sender_history(rd_history, rd_history_s, uid):
            continue
        
        return user 

g_log_path = "/data/log/weibo_forward_clicklike_hot/wb_clicklike_mobile.log"

def wb_process(mid,upnum,redisIns,rediskey):
    args={"rd_black_h":"127.0.0.1","rd_black_p":'6379',"rd_black_s":"weibo_black","rd_history_h":"127.0.0.1","rd_history_p":"6379","rd_history_s":"weibo_history_user_id","wb_omid":str(mid),"like_num":upnum,"timestart":0,"timeout":23,"gap":float(1),"remote_qusers":"remote_redis_file.list","log":True,"level":4} 
    log.setLoginfo(g_log_path, args["level"] ,args["log"])
    
    rd_black = RedisHelper(args["rd_black_h"], args["rd_black_p"]).get_conn()
    rd_history = RedisHelper(args["rd_history_h"], args["rd_history_p"]).get_conn()
    dr = Distributed(redis_file=args["remote_qusers"], timeout=args["timeout"]*3600)
    if not dr.init():
        sys.exit()
    
    like_ok = 0
    while like_ok < args["like_num"]:
        user = get_vaild_sender(dr, rd_black, args["rd_black_s"],
                rd_history, args["rd_history_s"], args["timestart"]*3600)
        
        util.is_continue()

        wl = WbLike(user)
        ret = wl.set_like(args["wb_omid"]) 
        if not ret:
            continue

        like_ok += 1
        redisIns.incr(rediskey)
        log.INFO('like_ok: %d' % like_ok)

        set_sender_history(rd_history, args["rd_history_s"], user['uid'])

        time.sleep(args["gap"])
def wb_main(processesnum,mid,upnum,redisIns,rediskey):
    #pro_pool=mp.Pool(processes = 10) 
    for i in range(int(processesnum)):
        #pro_pool.apply(wb_process,(mid,upnum,redisIns,rediskey,))
        p=mp.Process(target =wb_process, args = (mid,upnum,redisIns,rediskey,))
        p.start()
    #print "start"
    #pro_pool.close()
    #pro_pool.join()
    #print "stop"
#独立执行时操作
if __name__ == "__main__":
   # parser = argparse.ArgumentParser(description="""微博点赞""")
   # parser.add_argument('--rd-black-h', action="store", dest='rd_black_h',
   #         default='127.0.0.1', type=str,
   #         help='指定redis black server的ip,用于过滤黑名单,默认127.0.0.1')
   # parser.add_argument('--rd-black-p', action="store", dest='rd_black_p',
   #         default='6379', type=int, help='指定redis black server的端口,默认6379')
   # parser.add_argument('--rd-black-s', action="store", dest='rd_black_s',
   #         required=True, type=str, help='必须指定存放黑名单的集合名')
   # 
   # parser.add_argument('--rd-history-h', action="store", dest='rd_history_h',
   #         default='127.0.0.1', type=str, 
   #         help='指定redis history server的ip,用于记录历史用户信息,默认127.0.0.1')
   # parser.add_argument('--rd-history-p', action="store", dest='rd_history_p',
   #         default='6379', type=int, help='指定redis history server的端口,默认6379')
   # parser.add_argument('--rd-history-s', action="store", dest='rd_history_s',
   #         default='weibo_history_user_id', type=str,
   #         help='指定存放历史用户id的集合名,默认weibo_history_user_id')
   # 
   # parser.add_argument('--wb-omid', action="store", dest='wb_omid',
   #         required=True, type=str, help='必须指定要点赞的微博的omid')
   # parser.add_argument('--like-num', action="store", dest='like_num',
   #         default='100', type=int, help='指定点赞的数量,默认100')
   # parser.add_argument('-s', action="store", dest='timestart',
   #         default=5, type=int, help = '指定cookie开始时间,单位小时,默认5')
   # parser.add_argument('-t', action="store", dest='timeout',
   #         default=23, type=int, help = '指定cookie有效时间,单位小时,默认23')
   # parser.add_argument('-g', action="store", dest='gap',
   #         default='1', type=float, help='指定点赞间隔,单位秒,默认1.0')
   # 
   # parser.add_argument('--remote_qusers', action="store", dest='remote_qusers',
   #         default='remote_redis_file.list',
   #         help='程序轮询从远端redis读取用户信息,指定配置文件,默认./remote_redis_file.list')

   # parser.add_argument('-P', action="store_true", dest = 'log',
   #         default=False, help = '将打印信息输入到日志文件')
   # parser.add_argument('-l', action="store", dest='level',
   #         default=4, type=int, choices=(0,1,2,3,4),
   #         help='设置日志的级别, 1错误 2警告 3运行 4调试.默认4')
   # args = parser.parse_args(sys.argv[1:])
   # 
   # log.setLoginfo(g_log_path, args.level, args.log)
   # 
   # rd_black = RedisHelper(args.rd_black_h, args.rd_black_p).get_conn()
   # rd_history = RedisHelper(args.rd_history_h, args.rd_history_p).get_conn()
   # dr = Distributed(redis_file=args.remote_qusers, timeout=args.timeout*3600)
   # if not dr.init():
   #     sys.exit()
   # 
   # like_ok = 0
   # while like_ok < args.like_num:
   #     user = get_vaild_sender(dr, rd_black, args.rd_black_s,
   #             rd_history, args.rd_history_s, args.timestart*3600)
   #     
   #     util.is_continue()

   #     wl = WbLike(user)
   #     ret = wl.set_like(args.wb_omid) 
   #     if not ret:
   #         continue

   #     like_ok += 1
   #     log.INFO('like_ok: %d' % like_ok)

   #     set_sender_history(rd_history, args.rd_history_s, user['uid'])

   #     time.sleep(args.gap)
