#coding=utf-8
#!/usr/bin/env python

'''
游戏客户端起来后,打开共享内存 Lodoss 长度为 0xFF,0x10
寻找一个空位,写入自己的PID
'''



import os
import sys
import time
import threading


WG_CLIENT_LOGOUT    = -2
WG_CLIENT_WAITING   = 0
WG_CLIENT_NEEDSTART = 1
WG_CLIENT_LOGINING  = 2
WG_CLIENT_LOGINED   = 3
WG_CLIENT_ERROR     = 4


class CProcessManaget(threading.Thread):
    """docstring for CProcessManaget"""
    def __init__(self, client_manager):
        super(CProcessManaget, self).__init__()
        self.client_manager = client_manager
        self.thread_stop = False

    def run(self): #Overwrite run() method, put what you want the thread do here  
        while not self.thread_stop:  
            self.checkActiveClient()
            self.autoCreateGameProcess()
            time.sleep(5) 
    def stop(self):  
        self.thread_stop = True  

    #检查活动帐号并处理掉线的号
    def checkActiveClient(self):
        GameTime=time.time()
        for k in self.client_manager.clients:
            wg=self.client_manager.clients[k]
            if not wg.bNeedAutoLogin:
                continue
            if (GameTime > wg.last_active + 30 ):
                if wg.pid > 0:
                    #已经上线,但是40秒无消息的 #强行关闭进程
                    print("TASKKILL /PID %s  " % wg.pid,wg.last_active)
                    os.system("TASKKILL /PID %s /F /T" % wg.pid);
                    wg.pid=-3; #设置为无响应状态
                    print("重新登陆帐号:",wg.uid);
                    
                    wg.luaMSG["MSG"]="开始登陆"
                    self.client_manager.lock_needLogin.acquire()
                    self.client_manager.needLogin.append(wg)
                    self.client_manager.lock_needLogin.release()
        return 

#开启新进程
    def autoCreateGameProcess(self):
        if len(self.client_manager.config["path"]) <=0:
            return False;
        GameTime=time.time()
        if (GameTime < self.client_manager.lastCreateProcessTime + self.client_manager.config["intervalTime"] ):
            return False;
        #处理新登陆的号
        self.client_manager.lock_needLogin.acquire()
        for wg in self.client_manager.needLogin:
            print("wg:",wg.uid)
            if wg.state >= WG_CLIENT_NEEDSTART :
                if not wg.bNeedAutoLogin:
                    print("not wg.bNeedAutoLogin",wg.uid)
                    continue
                if wg.pid > 0:
                    print("wg.pid",wg.uid)
                    continue
                wg.state = WG_CLIENT_LOGINING
                wg.last_active=time.time()
                wg.note="启动进程..."
                cmd="start " + self.client_manager.config["path"]+" AutoInject"
                print("启动进程:",wg.uid,cmd,wg.last_active)
                os.system(cmd)
                self.client_manager.lastCreateProcessTime=GameTime
                break
        self.client_manager.lock_needLogin.release()
