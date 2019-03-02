import requests
from lxml import etree
import pickle,os,datetime,time,random
from urllib.parse import urljoin

class Proxy(object):
	def __init__(self):
		# 免费ip网点
		self.root_url = 'http://www.xicidaili.com/nn'
		# 请求头
		self.headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
			
		}
		# 存放 all_ip ,can_use_ip
		self.all_ip = []
		self.can_use_ip = []
		
	def download_page(self,url):
		'''
		:param url: url
		:return:
		'''
		r = requests.get(url,headers=self.headers)
		if r.status_code == 200:
			if len(r.text) >5000:
				return r.text
		else:
			print('发生错误，代码：{}'.format(r.status_code))
			
	def parse_ip_nextUrl(self,page):
		'''
		:param page:
		:return:  下一页的相对地址
		'''
		#print(page)
		if not page is None:
			html = etree.HTML(page)
			path_main = html.xpath('//table[@id="ip_list"]//tr')[1:]
			for i in path_main:
				host = i.xpath('./td[2]/text()')[0]
				port = i.xpath('./td[3]/text()')[0]
				proto = i.xpath('./td[6]/text()')[0]
				self.all_ip.append({proto:'{}:{}'.format(host,port)})
			next_url = html.xpath('//div[@class="pagination"]/a[last()]/@href')[0]
			return next_url
	
	def all_ip_size(self):
		'''
		:return:
		'''
		if self.all_ip is None:
			return
		return len(self.all_ip)
		
	
	def get_can_use_ip(self):
		'''
		:return:
		'''
		while self.all_ip_size():
			ip = self.all_ip.pop()
			#print(ip)
			# 字典键 与值 的获取 ，需要通过下面这种遍历的形式
			for i , j in ip.items():
				#print(i)
				#print(j)
			#proto ,host = ip.items()
				ip = {i:j}
			try:
				r = requests.get('https://www.baidu.com',headers = self.headers, proxies = ip,timeout=2)
				if r.status_code == 200:
					msg = '{}可用...'.format(ip)
					print(msg)
					self.log(msg)
					self.can_use_ip.append(ip)
			except Exception as e:
				msg = '{}不可用...'.format(ip)
				print(msg + '正准备测试下一个')
				self.log(msg)
				continue
	
	def can_use_ip_size(self):
		'''
		:return:
		'''
		return  len(self.can_use_ip)
	
	def log(self,msg):
		'''
		:param msg:
		:return:
		'''
		with open(r'ip_log.txt','a',encoding='utf-8') as f:
			f.write('\n【{}】{}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),msg))
	
	def store_ip(self):
		'''
		:return:
		'''
		
		print(self.can_use_ip)
		with open('can_use_ip.pickle','wb') as f:
			pickle.dump(self.can_use_ip,f)
			print('已存储。')
		
	# def load_ip(self,name):
	# 	'''
	# 	从本地加载ip，然后应用
	# 	:param name: 保存ip的文件名，包括后缀
	# 	:return: ip列表
	# 	'''
	# 	pickle_file = open(name,'wb')
	# 	ip_list = pickle.load(pickle_file)
	# 	return ip_list
	

	
	def crawler(self):
		'''
		:return:
		'''
		os.chdir(r'G:\others\otherItems\ip')
		msg = '开始本次ip爬虫...'
		self.log(msg)
		# 当can_use_ip 大小到达 200 时，则停止
		while self.can_use_ip_size() <= 100000:
			
			page = self.download_page(url=self.root_url)
			next_url = self.parse_ip_nextUrl(page)
			self.get_can_use_ip()
			self.root_url = urljoin(self.root_url,next_url)
			print('正在休息...')
			print('准备爬取【{}】...'.format(self.root_url))
			time.sleep(random.uniform(2,5))
			
		else:
			print('ip数量超过1000，准备关闭。')
			self.store_ip()
			msg = '本次爬取结束！ip已存入本地，可用ip数量为{}!'.format(self.can_use_ip_size())
			self.log(msg)
			

if __name__ == '__main__':
	p = Proxy()
	p.crawler()