#coding: utf-8

import requests, datetime, time, Queue, gevent, random, ConfigParser, random
from urllib import quote
from pyquery import PyQuery as pq

class ProxyVote(object):

    def __init__(self):
        '''
        初始化
        '''
        import gevent.monkey
        gevent.monkey.patch_socket()

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
            "success_flag": "",
            "floop_count": 2,
            "total_count": 100
        }
    
    
    def start(self):
        '''
        开始服务
        '''
        # 初始化参数
        self.get_options()
        
        # for i in range(self.options["floop_count"]):
        while self.okQueue.qsize() <= self.options["total_count"]:
            # 拿到代理
            self.get_proxies()
            
            # 使用gevent投票
            self.gevent_vote()
            
            self.proxyQueue = Queue.Queue()
            self.proxies = []
        
        print u"成功[ %s ]次, 失败[ %s ]次!" % (self.okQueue.qsize(), self.errQueue.qsize())
    
    
    def get_options(self):
        '''
        获取配置信息
        '''
        config = ConfigParser.SafeConfigParser()
        config.read("vote.ini")
        
        self.options.update({
            "vote_url": config.get("default", "vote_url").replace('TIME', str(random.randrange(1000000, 9999999))),
            "proxy_urls": config.get("default", "proxy_urls").split('|'),
            "max_thread": int(config.get("default", "max_thread")),
            "min_delay": int(config.get("default", "min_delay")),
            "max_delay": int(config.get("default", "max_delay")),
            "timeout": int(config.get("default", "timeout")),
            "success_flag": config.get("default", "success_flag"),
            "floop_count": int(config.get("default", "floop_count")),
            "total_count": int(config.get("default", "total_count"))
        })
    
    
    def get_proxy1(self, url):
        '''
        获取代理
        '''
        # 抓取代理地址
        req = requests.get(
            url,
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36'
            }
        )
        
        # 解析结果
        dom = pq(req.text)
        
        # 填充代理
        for x in dom('.table').eq(0).find('li.proxy'):
            
            self.proxies.append(x.text.strip())
            self.proxyQueue.put(x.text.strip())
    
    
    def get_proxy(self, url):
        '''
        获取代理
        '''
        # 抓取代理地址
        req = requests.get(
            url,
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36'
            }
        )
       
        
        # 填充代理
        for x in req.text.split('\r\n'):
            
            self.proxies.append(x.strip())
            self.proxyQueue.put(x.strip())
        

    def get_proxies(self):
        '''
        批量获取代理
        '''        
        for url in self.options["proxy_urls"]:
            try:
                time.sleep(2)
                self.get_proxy(url)
            except Exception, e:
                print e

        print u'共获取到[ %s ]个代理' % len(self.proxies)
        
    
    def vote_log(self, proxy, success=True):
        '''
        投票日志
        '''
        msg = u"成功"
        
        if success:
            self.okQueue.put(proxy)
        else:
            self.errQueue.put(proxy)
            msg = u"失败"
        
        print u'[ %s - %s - %s ]:使用代理[ %s ]%s!![%s]' % (self.okQueue.qsize(), self.errQueue.qsize(), self.okQueue.qsize() + self.errQueue.qsize(), proxy, msg, self.options["vote_url"].decode('utf-8'))
    
    
    def vote(self, proxy):
        '''
        '''
        
        # 间隔秒数
        time.sleep(
            random.randint(
                self.options["min_delay"], 
                self.options["max_delay"]
            )
        )
        
        try:
            # 代理投票
            req = requests.get(
                self.options["vote_url"], 
                proxies = {'http': 'http://%s' % proxy, 'https': 'http://%s' % proxy}, 
                headers = {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 7_0 like Mac OS X; en-us) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A465 Safari/9537.53'
                }, 
                timeout = self.options["timeout"]
            )
            cookies = req.cookies
            
            # 是否成功
            if req.text.find(self.options["success_flag"]) > -1:
                # 成功之后 模拟用户点击
                target_url = ''
                dom = pq(req.text)
                result = dom('#results .result')
                for i in range(len(result)):
                    
                    if result.eq(i).find('span.site').text().find(self.options["success_flag"]) > -1:
                        target_url = result.eq(i).find('a.result_title').attr('href')
                        break
                
                # 百度出的结果有时会去掉 http: 此处做下判断
                target_url = target_url if target_url.startswith('http') else ("http:"+target_url)
                # print target_url
                #time.sleep(1)
                
                req = requests.get(
                    target_url, 
                    proxies = {'http': 'http://%s' % proxy, 'https': 'http://%s' % proxy}, 
                    headers = {
                        'Referer': self.options["vote_url"],
                        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 7_0 like Mac OS X; en-us) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A465 Safari/9537.53'
                    }, 
                    cookies = cookies,
                    timeout = 15
                )
                
                if req.text.find(self.options["success_flag"]) > -1:
                    self.vote_log(proxy, True)
                    return True
                else:
                    self.vote_log(proxy, False)
                    return False
            else:
                self.vote_log(proxy, False)
                return False
                
        except Exception, e:
            # print e
            self.vote_log(proxy, False)
            return False
    
    def gevent_vote(self):
        '''
        '''
        def fetch(tid, max_count):
            count = 0
            print '线程[ %s ]开启...' % tid
            
            while count < max_count:
                proxy = self.proxyQueue.get()
                count += 1
                
                if self.vote(proxy):
                    print '追加一次'
                    time.sleep(2)
                    
                    if self.vote(proxy):
                        print '再追加一次'
                        time.sleep(2)
                        self.vote(proxy)
                        pass
                
                    
        
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
    
    
