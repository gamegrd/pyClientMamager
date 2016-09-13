#coding=utf-8
#!/usr/bin/env python
import tornado.ioloop
import tornado.iostream
import tornado.netutil
import tornado.web
import time
import datetime
import json
import tempfile
import codecs
import os
import sys
import copy
import threading
from  pyProecssManager import *





#获取脚本文件的当前路径 结尾不带 /
def cur_file_dir():
    #获取脚本路径
    path = sys.path[0]
    #判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.dirname(path)



class WGClient(object):
    def __init__(self, uid,pwd):
        self.uid =uid
        self.pwd =pwd
        self.name=""
        self.pid =0
        self.lv  =0
        self.money=0
        self.note=""
        self.client=None
        self.last_active =0
        self.bNeedAutoLogin = False
        self.cmd={};
        self.state = WG_CLIENT_WAITING
        self.luaMSG ={}

class CClientManager(object):
    def __init__(self):
        self.clients   = {}
        self.needLogin = []
        self.lock_needLogin = threading.Lock()
        self.lastCreateProcessTime=0;

        self.paraSDKMSG={
            "getAccount":self.getAccount,
            "report"    :self.report,
            "getState"  :self.getState,
            "loginIDList":self.loginIDList,
            "logOutIDList":self.logOutIDList,
            "workMode" : self.workMode,
            "changeGamePath":self.changeGamePath,
            "loginIntervalTime":self.loginIntervalTime,
            "getDefaultSetting":self.getDefaultSetting,
            "uploadAccounts": self.uploadAccounts,
        }
        
        self.config = self.loadConfig(r'/Config.json')
        if None == self.config:
            self.config={"intervalTime":30,"path":cur_file_dir()+r'/LoadDllx64.exe'}        

        pData=self.loadConfig(r"/uids.json")
        if None != pData:
            self.uploadAccounts(pData)

        self.ProcessManager=CProcessManaget(self)
        self.ProcessManager.start()

    def saveConfig(self,object,name):
        stream=json.dumps(object);
        filename = cur_file_dir()+ name
        file_object = open(filename,'w')
        file_object.write( stream )
        file_object.close( )

    def loadConfig(self,name):
        filename = cur_file_dir()+ name
        print("加载配置文件:",filename)
        try:
            if os.path.exists(filename):
                file_object = open(filename,'r')
                all_the_text = file_object.read( )
                file_object.close( )
                return json.loads(all_the_text)
        except:
            pass
        return None

    def add_user(self, uid, MSG):
        if 0==len(uid):
            return
        if not (uid in self.clients):
            self.clients[uid]=WGClient(uid,"")
        wg=self.clients[uid]
        wg.luaMSG=MSG
        wg.pid =MSG["pid"]
        wg.uid =MSG["uid"]
        wg.lv  =MSG["Lev"]
        wg.name=MSG["Name"]
        wg.money=MSG["Money"]
        wg.note=MSG["MSG"]
        wg.last_active = time.time();
        return wg

    def getAccount(self,msg):
        self.lock_needLogin.acquire()
        if 0==len(self.needLogin):
            self.lock_needLogin.release()
            return {"uid":"","pwd":""}
        rt=self.needLogin[0] 
        rt.pid=msg["pid"];
        del self.needLogin[0]
        self.lock_needLogin.release()
        print("分配帐号 pid : %d ,%s" % (rt.pid,rt.uid))
        return {"uid":rt.uid,"pwd":rt.pwd}


    #网页调用的sdk 返回各帐号状态
    def getState(self,pData):
        start = pData["start"]
        num   = pData["num"]
        if 0==num:
            num=len(self.clients)
        wgs =[]
        p=-1;
        
        for k in self.clients:
            p=p+1
            if ( start > p):
                continue
            num = num -1
            if (num < 0):
                break;
            wg=self.clients[k]
            wgs.append( {"uid":wg.uid,"pid":wg.pid,"lv":wg.lv,"money": wg.money ,"name":wg.name,"note":wg.note} )
            wgs=sorted(wgs, key = lambda x:x["uid"], reverse=False);
        return {"wgs":wgs,"total":len(self.clients)};
    
    def loginIDList(self,pData):
        print("登陆",pData)
        for uid in pData["IDList"]:
            wg=self.clients[uid]
            if 0==len(wg.pwd):
                continue
            if wg.state > WG_CLIENT_WAITING:
                continue
            wg.bNeedAutoLogin=True
            wg.state=WG_CLIENT_NEEDSTART;
            wg.cmd={}
            if wg.pid > 0:
                continue
            wg.note="开始登陆"
            print("收到登陆号",wg.uid)
            self.lock_needLogin.acquire()
            self.needLogin.append(self.clients[uid])
            self.lock_needLogin.release()
        return {"msg":"等待客户端上线"};

    def logOutIDList(self,pData):
        print("下线",pData)
        for uid in pData["IDList"]:
            self.clients[uid].cmd={"cmd":"logout","val":0,"pid":-1}
            self.clients[uid].state=WG_CLIENT_LOGOUT;
            self.clients[uid].note="开始下线"
            self.clients[uid].bNeedAutoLogin=False
        return {"msg":"下线命令已下达,等待下线"}

    def workMode(self,pData):
        for uid in pData["IDList"]:
            self.clients[uid].luaMSG["MSG"]="设置挂机模式"
            self.clients[uid].cmd={"cmd":"workMode","val":pData["val"]}
        return {"msg":"命令已下达,等待执行"}


    def changeGamePath(self,pData):        
        self.config["path"]=pData["path"];
        self.saveConfig(self.config, r'/Config.json')
        print("修改游戏路径:",pData["path"]);
        return {"msg":"路径修改成功,当前路径为:  "+self.config["path"]}

    def loginIntervalTime(self,pData):
        self.config["intervalTime"]=pData["val"];
        self.saveConfig(self.config, r'/Config.json')
        print("修改登陆间隔时间",str(self.config["intervalTime"]))
        return {"msg":"修改登陆间隔时间 :"+ str(self.config["intervalTime"]) }

    def getDefaultSetting(self,pData):
        return {"msg":"返回当前设置","cmd":"DefaultSetting","path":self.config["path"],"intervalTime":self.config["intervalTime"]}

    def uploadAccounts(self,pData):
        num=0;
        self.clients.clear()    #清除原有数据
        for account in pData["accounts"]:
            uid=account["uid"]
            pwd=account["pwd"]
            print ("添加帐号",uid, pwd)
            num=num+1
            WG=WGClient(uid,pwd)
            self.clients[uid]=WG
        self.saveConfig(pData,r"/uids.json")
        return {"msg":"上传成功,共 %d 组帐号" % (num) }

    def report(self,msg):
        wg = self.add_user(msg["uid"],msg)
        rt=copy.copy(wg.cmd)
        wg.cmd={}
        return rt;

    def  onSDKMSG(self,msg):
        #print("onSDKMSG",msg)
        return self.paraSDKMSG[msg["cmd"]](msg)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")




class sdkHandler(tornado.web.RequestHandler):
    def post(self):
        pData = self.get_argument('pData')
        #print("recv", pData)
        if pData != '':
            MSG = json.loads(pData)
            global client_manager
            respone=client_manager.onSDKMSG(MSG)
            #print("write",respone);
            self.set_header('Content-Type', 'application/json; charset=UTF-8')
            data=json.dumps(respone)
            self.write(data)
            #print("send " , data)


settings = {
"static_path" : cur_file_dir() + "/static"
}#配置静态文件路径
application = tornado.web.Application([
        (r"/", MainHandler),    
        (r"/sdk/?", sdkHandler),
        ],**settings)



client_manager = CClientManager()
print("编译时间:2015年7月8日 22:45:47")
try:
    application.listen(8888)

    print("\n\n服务已启动,请打开浏览器输入 http://127.0.0.1:8888 ")

    start_time = time.time()
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()
except Exception as e:
    print("服务启动失败,80端口被占用");
    os.system("pause")

