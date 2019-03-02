import requests,json
from fake_useragent import UserAgent
import hashlib
import pymongo
import time,datetime,os,random,csv,pickle


class Clawer(object):
	def __init__(self):
		self.new_tokens = set()
		self.old_tokens = set()
		self.new_tokens.add('li-xing-guo-78-60')
		# 当遇到错误，需要再次连接时，执行下面的代码，将上面3行代码注释掉，另外注释掉csv头部
		# self.new_tokens = self.load_file(r'G:\others\otherItems\zhihu\wait_use_token.txt')
		# self.old_tokens = self.load_file(r'G:\others\otherItems\zhihu\old_token.txt')
		
		# 连接数据库
		self.client = pymongo.MongoClient('localhost', 27017)
		self.db = self.client['spider']
		self.collection = self.db['zhihu']
		# 设置请求头
		self.ua = UserAgent()
		self.headers = {
			'User-Agent':self.ua.random,
			'accept': 'text / html, application / xhtml + xml, application / xml;q = 0.9, image / webp, image / apng, * / *;q = 0.8',
			'upgrade - insecure - requests': '1',
			'authority': 'www.zhihu.com',
			'accept - encoding': 'gzip, deflate, br',
			'accept - language': 'zh - CN, zh;q = 0.9',
			'cache - control': 'max - age = 0',
		}
		self.t_start = 0
		# 初始化 ip 生成器
		self.ip = self.load_ip()
		# 设置ip初始值
		self.proxies = None
		# 日志时间 ,并不会改变bug，
		#self.msg_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		# 给url计数
		self.count = 1
		# 统计发生错误的url换IP次数
		self.num = 0
		# 给csv准备的
		self.head_1 = ['name','gender','headline','answer_count','follower_count']
		self.head_2 = ['姓名','性别','简介','回答次数','关注者']
		
		
	def get_token_size(self):
		'''
		:return:
		'''
		if self.new_tokens is None:
			return
		return len(self.new_tokens)
	
	# token组成url
	def con_url(self):
		'''
		:return:
		'''
		token = self.new_tokens.pop()
		# 取出的token同时加入self.old.tokens中，用于去重验证
		m = hashlib.md5()
		m.update(token.encode('utf-8'))
		self.old_tokens.add(m.hexdigest()[8:-8])
		# token在下面组成url，1，2
		url_1 = 'https://www.zhihu.com/api/v4/members/{}/followers?include=data%5B*%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset=0&limit=20'.format(token)
		url_2 = 'https://www.zhihu.com/api/v4/members/{}/followees?include=data%5B*%5D.answer_count%2Carticles_count%2Cgender%2Cfollower_count%2Cis_followed%2Cis_following%2Cbadge%5B%3F(type%3Dbest_answerer)%5D.topics&offset=0&limit=20'.format(token)
		return [url_1, url_2]
	
	# 下载页面
	def download(self, url):
		'''
		:param url:
		:return:
		'''
		
		r = requests.get(url, headers=self.headers,proxies=self.proxies)
		if r.status_code == 200:
			self.t_start = time.time()
			return r.text
		# 如果错误代码为 403 ，那么就直接换IP重连
		elif r.status_code == 403:
			# 如果同一个url换IP次数超过5次，则丢弃该url
			if self.num <=5:
				t_end = time.time()
				# python 3.4.3以后 获取yield 值，使用__next__(),而不是 next()
				try:
					self.proxies = self.ip.__next__()
				except StopIteration:
					print('ip不够用了...')
					return 'ip done'
				self.log('\n【%s】上一个ip使用时长为：%s秒,下载%s页面时发生错误，错误码：%s --->>>准备第%s次更换ip,更换的ip为：【%s】...\n'%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),str(int(t_end) - int(self.t_start)),url,r.status_code,str(self.num+1),self.proxies))
				print('+++'*5 + '该URL：%s下载出现问题！！！'% url)
				print('上一个ip使用时长为：%s秒，正准备第%s次更换ip【%s】重连...'%(str(int(t_end) - int(self.t_start)),str(self.num+1),self.proxies))
				time.sleep(random.random())
				self.num += 1
				self.download(url)
			else:
				print('403以外的错误代码,丢弃该url...')
				return
		# 其他的错误代码，则丢弃该url
		else:
			return
			
			
	def load_ip(self):
		'''
		从本地加载ip
		:return: 单个ip
		'''
		try:
			with open(r'G:\others\otherItems\ip\can_use_ip.pickle', 'rb') as f:
				ip_list = pickle.load(f)
				for ip in ip_list:
					yield ip
		except EOFError:
			print('加载错误...正在重新加载！')
			self.load_ip()
			
	def load_file(self,path):
		'''
		:param path: 路径切记使用绝对路径
		:return:
		'''
		try:
			with open(path,'rb') as f:
				file = pickle.load(f)
				return file
		except EOFError:
			print('从本地加载失败...')
	
	# 解析出data，next_url
	def parse(self, page):
		'''
		:param page:
		:return:
		'''
		page = json.loads(page)
		datas = page.get('data')
		next_url = page.get('paging').get('next')
		return datas, next_url
	
	# 从data中解析出store_data ,token
	def parse_datas(self, datas):
		'''
		get store_data
		:param datas:
		:return:
		'''
		# store_data
		data = []
		tokens = []
		for i in datas:
			# 提取的数据 ： name: 昵称 , headline：个人简介 , gender：性别 , answer_count：回答数 ，follower_count：关注者
			token = i.get('url_token')
			tokens.append(token)
			name = i.get('name').encode('utf-8').decode('utf-8')  # 将unicode字符串编码为中文
			headline = i.get('headline').encode('utf-8').decode('utf-8')
			# 对headline判断
			if headline == '':
				headline = '未填写'
			answer_count = i.get('answer_count')
			follower_count = i.get('follower_count')
			gender = i.get('gender')
			# 判断性别 0 ， 1 ， -1
			if int(gender) == 0:
				gender = '女'
			elif int(gender) == 1:
				gender = '男'
			else:
				gender = '未填写'
			# data.append({'name': name, 'gender': gender, 'headline': headline, 'follower_count': follower_count, 'answer_count': answer_count})
			data.append(('('+ name + ')','('+gender+')','('+headline+')','('+str(answer_count)+')','('+str(follower_count)+')'))
		return data,tokens
	
	# 处理token列表，经过去重处理，存储token到 self.new_tokens
	def parse_token(self, token):
		'''
		去重 + 存token
		:param token:
		:return:
		'''
		for i in token:
			m = hashlib.md5()
			m.update(i.encode('utf-8'))
			token_md5 = m.hexdigest()[8:-8]
			if i not in self.new_tokens and token_md5 not in self.old_tokens:
				# self.store_token(i)
				self.new_tokens.add(i)
			else:
				self.get_repeat_token(i)
	
	# store_data
	def store_data(self, data):
		'''
		处理data
		:param data:
		:return:
		'''
		for i in data:
			self.collection.insert(i)
	# 保存 csv
	def store_csv(self,data):
		'''
		:param data:
		:return:
		'''
		with open(r'zhihu3_csv.csv','a',encoding='utf-8') as f:
			f_csv = csv.writer(f,)
			f_csv.writerows(data)
	# 保存mongodb
	def log(self,msg):
		'''
		:param msg:
		:return:
		'''
		with open(r'zhihu3_log.txt', 'a', encoding='utf-8') as f:
			f.write(msg)
	
	def get_repeat_token(self,token):
		with open(r'repeat_url_log3.txt', 'a', encoding='utf-8') as f:
			f.write('\n【%a】'% datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+ token)
		
	# def store_token(self,token):
	# 	with open(r'all_token_log3.txt', 'a', encoding='utf-8') as f:
	# 		f.write(token + '*****')
			
	# 递归爬取函数
	def spider(self, url):
		'''
		最主要的函数：递归爬取
		:param url:
		:return:
		'''
		page = self.download(url)
		if page is None:
			print('1')
			return
		if page == 'ip done':
			return 'over'
		print('下载第%s个URL：%s成功！准备解析...'% (self.count,url))
		# 发生错误的url经过换IP，重新连接之后，将其重置为 0
		self.num = 0
		datas, next_url = self.parse(page)
		if len(datas) != 0:
			# 这里的token 是一个列表，要能够直接加到self.tokens中去，还需要处理；同理 data也是一样
			# 因此需要另写两个函数。负责取出单个token，data
			datas,tokens = self.parse_datas(datas)
			#self.store_data(datas)
			self.store_csv(datas)
			self.parse_token(tokens)
			msg = '\n【%s】已存储%s个URL的下载数据'% (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),self.count)
			self.log(msg)
			self.count += 1
			time.sleep(random.uniform(1,5))
			return self.spider(next_url)
		else:
			print('[+++]datas为空！尝试另一条url线...')
	
	# 运行的主函数
	def main(self):
		'''
		:return:
		'''
		os.chdir(r'G:\others\otherItems\zhihu')
		t = False
		with open(r'zhihu3_csv.csv','a',encoding='utf-8') as f:
			f_csv = csv.writer(f)
			f_csv.writerow(self.head_2)
		msg = '\n'+'*' * 35 + '知乎爬虫日志' + '*' * 25
		self.log(msg)
		# 捕捉其它的错误，并在发生错误时，保存为使用的token，等待下次使用
		try:
			while self.get_token_size():  # 当self.new_tokens 为空时，跳出整个爬虫程序
				urls = self.con_url()
				for url in urls:
					xinxi = self.spider(url)
					if xinxi == 'over':
						t = True
						break
					time.sleep(random.randint(3,6))
				if t:
					print('正退出while循环中...')
					break
				time.sleep(random.uniform(5,8.6))
			else:
				# 如执行到这步，说明爬虫是正常结束的
				msg = '\n【%s】 爬取结束！数据量为：%s'% (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),len(self.old_tokens))
				self.log(msg)
			# 保存下载进度
			print('已保存wait_use_token,old_token文件可查看下载进度。')
			with open(r'G:\others\otherItems\zhihu\wait_use_token.txt', 'wb') as f:
				pickle.dump(self.new_tokens, f)
			with open(r'G:\others\otherItems\zhihu\old_token.txt', 'wb') as f:
				pickle.dump(self.old_tokens, f)
					
		except Exception as e:
			# 发生错误同样保存下载进度
			msg ='\n【{0}】遇到意料之外的错误：{1},剩余token量为：{2},正在保存old_token和未使用的token...'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),e,self.get_token_size())
			print(msg)
			self.log(msg)
			with open(r'G:\others\otherItems\zhihu\wait_use_token.txt','wb') as f:
				pickle.dump(self.new_tokens,f)
			with open(r'G:\others\otherItems\zhihu\old_token.txt','wb') as f:
				pickle.dump(self.old_tokens,f)
			
					
if __name__ == '__main__':
	c = Clawer()
	c.main()