#coding: utf-8
import requests, datetime, time, Queue, gevent, random, ConfigParser, random, datetime
from urllib import quote
from pyquery import PyQuery as pq

import gevent.monkey
gevent.monkey.patch_socket()

class ProxyVote(object):
    
    def __init__(self, name, target_count, vote_url, proxy_urls, flag, total_hour):
        '''
        '''
        self.name = name
        self.target_count = random.randint(850, 1400) # target_count
        self.vote_url = vote_url
        self.proxy_urls = proxy_urls
        self.flag = flag
        self.total_hour = total_hour
        
        self.proxies = []
        self.total = 0
        self.success = 0
        self.fail = 0
        self.start_time = datetime.datetime.now()
    
    
    def get_proxies(self):
        '''
        获取代理
        '''
        self.proxies = []
        
        for url in self.proxy_urls:
            
            gevent.sleep(1.2)
            
            try:
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
            except Exception, e:
                print e
        
        print (u"[ %s ]抓取到[ %s ]个代理" % (self.name, len(self.proxies))).encode('utf-8')
    
    
    def vote_log(self, proxy, flag):
        self.total += 1
        msg = u"成功!!"
        
        if flag:
            self.success += 1
            print (u"\033[1;32;40m [ %s - %s - %s - %s ]使用[ %s ]代理%s \033[0m" % (self.name, self.success, self.fail, self.total, proxy, msg)).encode('utf-8')
        else:
            self.fail += 1
            msg = u"失败"
            print (u"\033[1;31;40m [ %s - %s - %s - %s ]使用[ %s ]代理%s \033[0m" % (self.name, self.success, self.fail, self.total, proxy, msg)).encode('utf-8')
        
    
    
    def _vote(self, proxy):
        try:
            gevent.sleep(random.randint(4, 8))
            
            # 首先访问百度的页面主要是获取cookies
            req = requests.get(
                self.vote_url, 
                proxies = {'http': 'http://%s' % proxy, 'https': 'http://%s' % proxy}, 
                headers = {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 7_0 like Mac OS X; en-us) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A465 Safari/9537.53'
                }, 
                timeout = 15
            )
            cookies = req.cookies
            
            # 找出要点击的url
            target_url = ''
            dom = pq(req.text)
            result = dom('#results .result')
            for i in range(len(result)):
                
                if result.eq(i).find('span.site').text().find(self.flag) > -1:
                    target_url = result.eq(i).find('a.result_title').attr('href')
                    break
                    
            # 百度出的结果有时会去掉 http: 此处做下判断
            target_url = target_url if target_url.startswith('http') else ("http:"+target_url)
            
            #print target_url
            
            # 访问目标url
            req = requests.get(
                target_url, 
                proxies = {'http': 'http://%s' % proxy, 'https': 'http://%s' % proxy}, 
                headers = {
                    'Referer': self.vote_url,
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 7_0 like Mac OS X; en-us) AppleWebKit/537.51.1 (KHTML, like Gecko) Version/7.0 Mobile/11A465 Safari/9537.53'
                }, 
                cookies = cookies,
                timeout = 15
            )
            
            # 检测访问是否成功
            if req.text.find(self.flag) > -1:
                self.vote_log(proxy, True)
                return True
            else:
                self.vote_log(proxy, False)
                return False
            
        except Exception, e:
                #print e
                self.vote_log(proxy, False)
                return False
        
        
        
    def vote(self):
    
        # 获取代理
        self.get_proxies()
        
        for proxy in self.proxies:
            if self._vote(proxy):
                print u'追加一次'.encode('utf-8')
                if self._vote(proxy):
                    print u'再追加一次'.encode('utf-8')
                
    
    def start(self):
        '''
        '''
        print (u'-------------------开始处理[ %s ]的投票-------------------' % self.name).encode('utf-8')
        gevent.sleep(random.randint(10, 200))
        # 循环开始投票
        while (datetime.datetime.now() - self.start_time).total_seconds() < self.total_hour*3600:
            gevent.sleep(0.5)
            if self.success < self.target_count:
                self.vote()
            else:
                break
        
        print (u'[ %s ]的投票结果: 成功 [ %s ], 失败 [ %s ], 总次数[ %s ]' % (self.name, self.success, self.fail, self.total)).encode('utf-8')
        print (u'-------------------处理[ %s ]的投票结束-------------------' % self.name).encode('utf-8')
    
    
    
    
        
        
        
if __name__ == "__main__":

    print u'开始...'.encode('utf-8')

    config = ConfigParser.SafeConfigParser()
    try:
        config.read("zhixuan.ini")
    except Exception, e:
        print e
        config.read("/var/www/ProxyVote/zhixuan.ini")
        
    threads = []
    for section in config.sections():
        
        threads.append(
            gevent.spawn(
                ProxyVote(
                    section.decode('utf-8'), 
                    int(config.get(section, "total_count")),
                    config.get(section, "vote_url").replace('TIME', str(random.randrange(1000000, 9999999))),
                    config.get(section, "proxy_urls").split('|'),
                    config.get(section, "success_flag"),
                    int(config.get(section, "total_hour"))
                ).start
            )
        )
    
    gevent.joinall(threads)
    
    
    
    
    
    
    
    
    
    
