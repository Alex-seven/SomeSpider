import requests
from lxml import etree
from fake_useragent import UserAgent
import re
import time
import random
import csv,os

def zufang_58():
	# 存放 房源信息 详情
	info_58 = []
	# 共 5 页
	for i in range(1,6):
		if i == 1:
			url = 'http://gy.58.com/guanshanhuqita/hezu/'
		else:
			url = 'http://gy.58.com/guanshanhuqita/hezu/pn' + str(i) + '/'
		html = get_html(url)
		list_ = html.xpath('//ul[@class="listUl"]//li')
		for each in list_[0:-2]:
			# 有些地址在a/text里，有些在p/text里，分开求
			locations = each.xpath('.//p[@class="add"]//a[2]/text()')
			if locations:
				location = re.sub(r'\.','',locations[0])
			else:
				locations = each.xpath('.//p[@class="add"]/text()')
				location = re.sub(r'[\.\n;&]', '', locations[1].strip())
			price = each.xpath('.//div[@class="money"]/b/text()')[0]
			house_link = each.xpath('.//div[@class="img_list"]/a/@href')[0][2:]
			info_58.append((price,location,house_link))
			time.sleep(0.1)
	print('爬取【58同城】结束，本次总共爬取【5】页！房源总数【{}】个'.format(len(info_58)))
	return info_58
	

'''
关于贵阳观山湖区租房信息解析完成，下一步，导入高德地图，可视化！！！
'''
def zufang_ajk(url=None,info_ajk=None,count=None):
	# info_ajk = []  放在这里会被重新赋为 空列表 ,所以把它放在本函数参数；count也一样，【count用于计页数】
	html = get_html(url)
	list_ = html.xpath('//div[@class="zu-itemmod  "]')# 这里网站做了干扰，定位的class值会变，将网页下载到本地，查看解决
	for each in list_:
		house_link = each.xpath('./a[1]/@href')[0]
		price = each.xpath('.//div[@class="zu-side"]/p/strong/text()')[0]
		try:
			location = each.xpath('.//address[@class="details-item"]/a/text()')[0]# 爬到一半这里突然出现list index out of range 错误
		except Exception :
			location = '没有定位到'
		info_ajk.append((price,location,house_link))

		time.sleep(0.3)

	# 获取下一页链接
	next_url = html.xpath('//div[@class="page-content"]/div/a[@class="aNxt"]/@href')
	# 判断是否还有下一页，有则提示爬取开始，否则提示爬取任务结束
	if len(next_url) == 0:
		print('爬取【安居客】结束，本次总共爬取【{}】页！房源总数【{}】个'.format(count, len(info_ajk)))
		return info_ajk
		
	else:
		count += 1
		# info_ajk =  info_ajk
		t = random.uniform(0.5, 2.9)
		print('{}秒后前往安居客【第{}页】爬取内容！'.format(t, count))
		time.sleep(t)
		# 使用递归做个翻页的功能
		return zufang_ajk(url=next_url[0], info_ajk=info_ajk,count=count) # 这里要想继续跑函数 ，记得要返回！！
		
		
def save_csv(rows):
	headers = ['价格','地点','房子链接']
	os.chdir(r'c:\users\yfg\desktop')
	with open('gyRoomInfo.csv','w',encoding='utf-8') as f:
		f_csv = csv.writer(f,)
		f_csv.writerow(headers)
		f_csv.writerows(rows)

def get_html(url):
	ua = UserAgent()
	headers = {'User-Agent': ua.random}
	r = requests.get(url=url, headers=headers)
	return etree.HTML(r.text)

def main():
	# 容纳 58 、安居客 房源信息列表
	all_info = []
	# 函数 info_ajk 三个参数
	info_ajk = []
	count = 1
	url_1 = 'https://gy.zu.anjuke.com/fangyuan/guanshanhu/fx1/'
	# 两个爬取房源函数实例化
	print('开始爬取【安居客第一页】--->>>【贵阳观山湖房源】')
	info_1 = zufang_ajk(url=url_1,info_ajk=info_ajk,count=count) # 千万不要将变量命名为 info_ajk ，不然外部变量会覆盖内部变量，
	print(len(info_1))
	print('开始爬取【58同城】--->>>【贵阳观山湖房源】')        # 功亏一篑！！！
	info_2 = zufang_58()
	print(len(info_2))
	# 以 extend 方法将58、安居客房源信息导入总列表
	all_info.extend(info_1)
	all_info.extend(info_2)
	print(len(all_info))
	all_info = list(set(all_info))
	print(len(all_info))
	print(all_info[:10])
	# 存为 CSV
	try:
		save_csv(sorted(all_info,key=lambda price:price[0]))
	except TypeError as e:
		print(e)
		pass
#以上步骤完成后 出现了语法错误 ，从68line开始，注释掉错误的地方，报错的位置却又后退一格
#  终于找到原因这是  print（）  少了一个括号！！！  print 少括号的错误，真是烦，都不会提醒你地方的！！
if __name__ == '__main__':
	time.clock()
	main()
	print('爬取共持续【{}】！'.format(time.clock()))