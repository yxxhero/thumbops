#!/usr/bin/env python2.7
#coding:utf-8
#thumb platform
from flask import Flask 
from flask import session,redirect,url_for,escape
from flask import request
from flask import render_template
from flask import jsonify,abort
from functools import wraps
from model import db,app,tasklist
from pyquery import PyQuery as pq
import requests
import psutil
import json
import time
import logging
import hashlib   
import redis


import sys
reload(sys)
sys.setdefaultencoding('utf-8')

#日志模式初始化
logging.basicConfig(level="DEBUG",
                format='%(asctime)s  %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                filename='./log/debug.log',
                filemode='a')

def str2stamp(timestr):
    return time.mktime(time.strptime(timestring, '%Y-%m-%d %H:%M:%S'))

#Get mid
def Get_Mid(wburl):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36','Cookie':'UOR=www.techweb.com.cn,widget.weibo.com,www.techweb.com.cn; YF-Ugrow-G0=ad06784f6deda07eea88e095402e4243; SUB=_2AkMtehitf8NxqwJRmPkWz2Lga4t1yA_EieKbJul2JRMxHRl-yT9kqkIftRB6Bvo2QlbRBPxZKBux9MPXb6lry2IuJE_1; SUBP=0033WrSXqPxfM72-Ws9jqgMF55529P9D9WhPG6fzg9x..jgixRu1hBeq; login_sid_t=b5b2a5f785fe933c74cf5b9822f2729f; YF-V5-G0=c99031715427fe982b79bf287ae448f6; _s_tentry=passport.weibo.com; Apache=7793085729420.195.1512478628252; SINAGLOBAL=7793085729420.195.1512478628252; ULV=1512478628261:1:1:1:7793085729420.195.1512478628252:; YF-Page-G0=b98b45d9bba85e843a07e69c0880151a; WBStorage=82ca67f06fa80da0|undefined; cross_origin_proto=SSL'}
    r = requests.get(wburl, headers=headers,timeout=4)
    midkey=pq(r.text)("script:contains('pl.content.weiboDetail.index')").text()
    title=pq(r.text)("meta[name='description']").attr["content"]
    jsonkey=midkey.split("FM.view(")[1].rstrip(")")
    midinfo=pq(json.loads(jsonkey)["html"])('.WB_handle')('li:last')('a').attr["action-data"]
    midnum=midinfo.split('&')[2].split("=")[1]
    return midnum,title

def Md5value(strvalue):
    m2 = hashlib.md5()   
    m2.update(strvalue)   
    return m2.hexdigest()
def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        print session.get("logged_in")
        if session.get("logged_in") and session.get("username") != None:
            return func(*args, **kwargs)
        return redirect(url_for('login', next=request.url))
    return decorated_function


#初始化redis连接池
redis_pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
#Get_Mid("https://weibo.com/3282913214/FyeiGzfta?ref=feedsdk&type=comment#_rnd1512532852183")

@app.route('/',methods=['GET'])
@login_required
def index():
    return  render_template("index.html",username=session['username'])

@app.route('/api/checkproc',methods=['GET'])
@login_required
def checkproc():
    processName="taskhandle"
    pids = psutil.pids()
    for pid in pids:
        p = psutil.Process(pid)
        if p.name() == processName:
	    return jsonify({"error":0}) 
    return jsonify({"error":1})		

@app.route('/login',methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.values['name'] != app.config['USERNAME']:
            error='Invalid username'
            print error
        elif request.values['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
            print error
        else:
            print "yes"
            session['logged_in'] = True
            session['username'] = request.values['name']
            return redirect(url_for("index"))
            print "yes"
    return render_template("login.html")

@app.route('/logout')
def loginout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for("login"))


@app.route('/home',methods=['GET'])
@login_required
def home():
    return  render_template("home.html")

@app.route('/list',methods=['GET'])
@login_required
def list():
    return  render_template("lists.html")

@app.route('/taskhandle',methods=['POST'])
@login_required
def taskhandle():
    method=request.form.get('method')
    if method == "start":
        try:
            tid=request.form.get("id")
            mod = tasklist.query.filter_by(id=tid).first()
            processesnum=mod.processesnum
            upnum=mod.upnum
            wbmid=mod.taskid
            rediskey=str(mod.create_time)+str(wbmid)
            if mod.status==1:
                return jsonify({"error":1,"msg":"任务已经启动，正在处理中...."})
            elif mod.status==2:
                return jsonify({"error":1,"msg":"任务已经处理完成...."})
            else:
                rins = redis.Redis(connection_pool=redis_pool)
                rins.set(rediskey,0)
                rins.lpush("taskqueue","^".join([str(processesnum),str(wbmid),str(upnum),str(rediskey)]))
        except Exception as e:
            print e
            return jsonify({"error":1,"msg":str(e)})
        else:
            mod.status=1
            db.session.commit()
            return jsonify({"error":0,"msg":"任务启动成功...."})

    elif method == "del":
        try:
           tid=request.form.get("id")
           mod = tasklist.query.filter_by(id=tid).first() 
           db.session.delete(mod)
           db.session.commit()
        except Exception as e:
            return jsonify({"error":1,"msg":str(e)})
        else:
            return jsonify({"error":0,"msg":"记录删除成功...."})

@app.route('/handle',methods=['POST'])
@login_required
def handle():
    try:
        processesnum=request.form.get("processesnum")
        wbmid=request.form.get("wbmid")
        upnum=request.form.get("upnum")
        if not all([processesnum,wbmid,upnum]):
            return jsonify({"error":1,"msg":"请检测您的输入"})
        else:
            mid,title=Get_Mid(wbmid)
            create_time=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
            db.session.add(tasklist(taskid=mid,wburl=wbmid,processesnum=processesnum,title=title,upnum=upnum,create_time=create_time))
            db.session.commit()
    except Exception as e:
        return jsonify({"error":1,"msg":str(e)})
    else: 
        return jsonify({"error":0,"msg":"任务添加成功...."})
@app.route("/tasklist",methods=["GET"])
def tasklistinfo():
    statusdic={1:'<button class="layui-btn layui-btn-xs">进行中</button>',2:'<button class="layui-btn layui-btn-xs layui-btn-danger">已完成</button>',0:'<button class="layui-btn layui-btn-xs layui-btn-normal">未启动</button>'}
    taskinfo={}
    taskinfo["data"]=[]
    try:
        task_list=tasklist.query.all()
        for item in task_list:
           rediskey=str(item.create_time)+str(item.taskid)
           rins = redis.Redis(connection_pool=redis_pool)
           if rins.get(rediskey) == None:
               likenum=0
           else:
               likenum=rins.get(rediskey)
           total=item.processesnum*item.upnum
           pcent=str(float(likenum)/float(total)*100)+"%"
           item.percent=pcent
           db.session.commit()
           taskinfo["data"].append({"id":item.id,"date":str(item.create_time),"taskid":item.taskid,"total":total,"percent":pcent,"title":"<a target='_blank' href="+item.wburl+">"+item.title+"</a>","status":statusdic[item.status]}) 
    except Exception as e:
        logging.error(str(e))
        taskinfo["code"]=1
        taskinfo["msg"]=""
        taskinfo["count"]=1000
        taskinfo["data"]=[]
        return jsonify(taskinfo)
    else:
        taskinfo["code"]=0
        taskinfo["msg"]=""
        taskinfo["count"]=1000
        return jsonify(taskinfo)


if __name__=='__main__':
    app.run(host="0.0.0.0",port=9999,debug=True)
