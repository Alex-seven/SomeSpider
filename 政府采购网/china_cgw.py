import requests
from lxml import etree
import re,csv,time,random,os


# get_first_page , get_other_page,get_detail_id 都只是为了获得所有 id，id是构建获取数据链接的参数
def get_first_page(url):
	r = s.get(url=url,headers=headers)
	return r.text
def get_other_page(url,page_num):
	datas = {
		'orgName':'',
		'enforceUnit':'',
		'punishTime':'',
		'punishTimeMax':'',
		'gp': page_num
	}
	r = s.post(url= url,data=datas,headers=headers)
	return r.text
def get_detail_id(page,list_ids):
	html = etree.HTML(page)
	detail_ids = html.xpath('//div[@class="gg_nr"]//tr[@class="trShow"]//a//@onclick')
	compile =  r"detail\('(\w+?)'\);"
	for i in detail_ids:
		id = re.findall(compile,i)
		list_ids.append(id)

# 下载data
def get_data(id_list):
	# 得到数据
	n = 1
	save_list = []
	for ids in id_list:
		print('开始下载第%d个...' % n)
		for id in ids:
			url2 = 'http://www.ccgp.gov.cn/cr/list/detail?id=%s' % id
		print(url2)
		headers2 = {
			'Connection': 'keep-alive',
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
			'Host': 'www.ccgp.gov.cn'
		}
		r = s.get(url=url2, headers=headers2)
		print(r.status_code)
		html = etree.HTML(r.text)
		data_all = [i.strip() for i in html.xpath('//table[@id="detail"]//tr//td[@class="inputTd"]//text()')]
		print(data_all)
		save_list.append((data_all[0], data_all[1], data_all[2], data_all[3], data_all[4], data_all[5], data_all[6],data_all[7], data_all[8], data_all[9]))
		print('已写入...')
		print('休息一会...')
		time.sleep(random.randint(5, 12))
		n += 1
	# 保存
	headers = ['企业名称', '统一社会信用代码', '企业地址', '严重违法失信行为的具体情形', '处罚结果', '处罚依据 ', '公布日期', '处罚日期', '公布截至日期', '执法单位']
	os.chdir(r'c:\users\yfg\desktop')
	with open('china_cgw.csv', 'w', encoding='utf-8') as f:
		file = csv.writer(f,)
		file.writerow(headers)
		file.writerows(save_list)
			
		
if __name__ == "__main__":
	url = 'http://www.ccgp.gov.cn/cr/list'
	headers = {
		'Connection': 'keep-alive',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
		'Host': 'www.ccgp.gov.cn'
	}
	s = requests.session()
	list_ids = []
	get_detail_id(get_first_page(url),list_ids)
	for page_num in range(2,7):
		get_detail_id(get_other_page(url,page_num),list_ids)
	print('ID数量为：%d'%len(list_ids))
	get_data(list_ids)
	