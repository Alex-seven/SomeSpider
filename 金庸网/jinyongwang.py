import requests, os, time
from lxml import etree

# 得到html页面
def get_html(url, headers):
	return etree.HTML(requests.get(url = url, headers = headers).text)

# 解析得到每本书的url 和 书名 和 书封面图片
def parse_book_url(html):
	book_urls = html.xpath(r'//ul[@class="list"]//p[@class="title"]//a//@href')
	book_titles = html.xpath(r'//ul[@class="list"]//p[@class="title"]//a//text()')
	book_imgs = html.xpath(r'//ul[@class="list"]//p[@class="img pu_bookrotate"]//img//@src')
	return (book_urls, book_titles, book_imgs)

# 解析得到每个章节的url 和 标题
def parse_chapter_url(html):
	chapter_urls = html.xpath(r'//ul[@class="mlist"]//li//a//@href')
	chapter_titles = html.xpath(r'//ul[@class="mlist"]//li//a//text()')
	return (chapter_urls, chapter_titles)

# 解析得到每个章节的内容
def parse_content(html):
	contents = html.xpath(r'//div[@id="vcon"]//p//text()')
	return contents

# 下载文本
def save_text(name, contents):
	with open('{}.txt'.format(name),'w', encoding = 'utf-8') as f:
		f.write(contents)
	print('{}下载完成！'.format(name))

# 下载封面
def save_img(name, img_url):
	contents = requests.get(img_url,
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
		AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}).content
	with open('{}.jpg'.format(name),'wb') as f:
		f.write(contents)
	print('{}封面下载完成！'.format(name))	

# 主逻辑函数
def main(url, headers):
	book_urls, book_titles, book_imgs = parse_book_url(get_html(url, headers))
	if len(book_urls) == 0:
		print('xpath has failed!')
	book_length = len(book_urls)
	for i in range(book_length):
		dir_1 = book_titles[i]
		# 拼接封面url
		img_url = root_url + book_imgs[i]
		# 下载封面
		save_img(book_titles[i], img_url)
		# 给每本书建dir
		os.mkdir(dir_1)
		# 切换dir到每本书dir下
		os.chdir(dir_1)
		# 拼接book_urls中的相对url为完整路径url：book_url
		book_url = root_url + book_urls[i]
		# 更改headers的Referer
		headers['Referer'] = url
		chapter_urls, chapter_titles = parse_chapter_url(get_html(book_url, headers))
		chapter_length = len(chapter_urls)

		for j in range(chapter_length):
			content_url = root_url + chapter_urls[j]
			# 再次更改headers的Referer
			headers['Referer'] = book_url
			contents = parse_content(get_html(content_url, headers))
			# 删除小说的空白段落
			contents = '\n'.join(contents).replace('\n', '')
			# 下载小说
			save_text(chapter_titles[j], contents)
			time.sleep(0.5)
		time.sleep(1.1)
		os.chdir(os.path.dirname(os.getcwd()))


if __name__ == "__main__":
	root_url = 'http://www.jinyongwang.com'
	url = 'http://www.jinyongwang.com/book/'
	# 构建headers
	headers = {
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
		'Accept-Encoding': 'gzip, deflate',
		'Accept-Language': 'zh-CN,zh;q=0.9',
		'Cache-Control': 'max-age=0',
		'Connection': 'keep-alive',
		'Host': 'www.jinyongwang.com',
		'Referer': '',   #后续按深度添加不同Referer
		'Upgrade-Insecure-Requests': '1',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
	}
	main(url, headers)