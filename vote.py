#coding: utf-8

import requests, datetime, time, Queue, gevent, random, ConfigParser
from pyquery import PyQuery as pq

import gevent.monkey
gevent.monkey.patch_socket()


class ProxyVote(object):

    def __init__(self):
        '''
        初始化
        '''
        self.proxyQueue = Queue.Queue()
        self.okQueue = Queue.Queue()
        self.errQueue = Queue.Queue()
        self.proxies = []
        self.options = {
            "vote_url": "",
            "proxy_urls": [],
            "max_thread": 2,
            "min_delay": 5,
            "max_delay": 15,
            "timeout": 15,
            "success_flag": ""
        }
        
        
    
    
    def start(self):
        '''
        开始服务
        '''
        # 初始化参数
        self.get_options()
        
        # 拿到代理
        self.get_proxies()
        
        # 使用gevent投票
        self.gevent_vote()
        
        print u"成功[ %s ]次, 失败[ %s ]次!" % (self.okQueue.qsize(), self.errQueue.qsize()) 
    
    
    def get_options(self):
        '''
        获取配置信息
        '''
        config = ConfigParser.SafeConfigParser()
        config.read("vote.ini")
        
        self.options.update({
            "vote_url": config.get("default", "vote_url"),
            "proxy_urls": config.get("default", "proxy_urls").split('|'),
            "max_thread": int(config.get("default", "max_thread")),
            "min_delay": int(config.get("default", "min_delay")),
            "max_delay": int(config.get("default", "max_delay")),
            "timeout": int(config.get("default", "timeout")),
            "success_flag": config.get("default", "success_flag")
        })
    
    
    def get_proxy(self, url):
        '''
        获取代理
        '''
        # 抓取代理地址
        req = requests.get(url)
        
        # 解析结果
        dom = pq(req.text)
        
        # 填充代理
        for x in dom('.cont_font').find('p').html().split('<br />&#13;'):
            self.proxies.append(x.split('@')[0].strip())
            self.proxyQueue.put(x.split('@')[0].strip())
        

    def get_proxies(self):
        '''
        批量获取代理
        '''        
        for url in self.options["proxy_urls"]:
            self.get_proxy(url)

        print u'共获取到[ %s ]个代理' % len(self.proxies)
        
    
    def vote_log(self, proxy, success=True):
        '''
        投票日志
        '''
        total = self.okQueue.qsize() + self.errQueue.qsize()
        
        if success:
            self.okQueue.put(proxy)
            print u'%s-哦也, 使用代理[ %s ]成功!!' % (total, proxy)
        else:
            self.errQueue.put(proxy)
            print u'%s-靠, 使用代理[ %s ]失败!!' % (total, proxy)
    
    
    def gevent_vote(self):
        '''
        '''
        def fetch(tid, max_count):
            count = 0
            print '线程[ %s ]开启...' % tid
            
            while count < max_count:
            
                # 间隔秒数
                time.sleep(
                    random.randint(
                        self.options["min_delay"], 
                        self.options["max_delay"]
                    )
                )
                
                count += 1
                proxy = self.proxyQueue.get()
                
                try:
                    # 代理投票
                    req = requests.get(
                        self.options["vote_url"], 
                        proxies = {'http': 'http://%s' % proxy}, 
                        headers = {
                            'Referer': 'http://www.baidu.com',
                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36'
                        }, 
                        timeout = self.options["timeout"]
                    )
                    
                    # 是否成功
                    if req.text.find(self.options["success_flag"]) > -1:
                        self.vote_log(proxy, True)
                    else:
                        self.vote_log(proxy, False)
                        
                except Exception, e:
                    # print e
                    self.vote_log(proxy, False)
                    
        
        # gevent配置
        threads = []
        max_thread = self.options["max_thread"]
        max_length = len(self.proxies)
        step = max_length / max_thread
        for i in range(0, max_thread):
            threads.append(
                gevent.spawn(
                    fetch, 
                    i, 
                    step
                )
            )
            
        gevent.joinall(threads)
    

if __name__ == "__main__":
    print u'开始...'
    ProxyVote().start()
    # go_page(url, get_proxies()[:20])
    
    # gevent_go_page(url, get_proxies()[:20])
    
    # print u"成功[ %s ]次, 失败[ %s ]次!" % (okQueue.qsize(), errQueue.qsize()) 
    
    
