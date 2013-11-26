import os.path, httplib2, logging, re

from BeautifulSoup import BeautifulSoup, Tag

from SOLUser import SOL_User as SOLUser

import htmllib
import re

link_re = re.compile(r'/(?P<url>(sex-)?s(tory)?)/(?P<story>\d+):(?P<chapter>\d+|i);?(?P<page>\d*)')

def parse_link(href):
	m = link_re.search(str(href))
	if m:
		story = m.group('story')
		chapter = m.group('chapter')
		return (story, chapter)
	else:
		return None


def unescape(s):
	p = htmllib.HTMLParser(None)
	p.save_bgn()
	p.feed(s)
	return p.save_end()

	
class SOLStory:
	base_url = 'http://storiesonline.net'
			
	@property
	def chapter_count(self):
		return len(self.links)
	
	def __init__(self, story_id):
		logging.debug('initializing story object (id: %d)' % story_id)
		self.story_id = story_id
		self.headers = None
		self.links = []
		self.title = ""
		self.author = ""
		
		self.http = httplib2.Http()
		user = SOLUser('blueboy88', 'vomisa')
		self.headers = user.GetHeaders(self.http)
		
		self.parseIndex()
		
	def getContent(self, page_url):
		logging.debug('fetching URL = %s', page_url)
		
		response, content = self.http.request(self.base_url + page_url, 'GET', headers=self.headers)
		
		logging.debug('response(%s|%s)', response['status'], response['content-type'])

		return content
		
	def getIndexLink(self):
		return  '/s/%s' % self.story_id
		
	def getIndexContent(self):
		url = self.getIndexLink()
		
		return self.getContent(url)
		
	def parseIndex(self):
		content = self.getIndexContent()
			
		soup = BeautifulSoup(content)
		
		title = soup.findAll('title')[0].string
		title = title.replace(" (Page 1) ", "")
		try:
			logging.debug("title string: %s" % title)
			author, sep, title = title.partition(': ')
			logging.debug("author: '%s' title: '%s'" % (author, title))
			title = unescape(title)
		except:
			n = title.find(' by ')
			author = title[n+4]
			title = title[:n]
			
			rx = re.compile('\s*\([^)]*\)')
			author = rx.sub('', author)
			
		self.author = author
		self.title = title.replace(" (Page 1)", " ").strip()
		
		logging.debug("(after normalize) author: '%s' title: '%s'" % (self.author, self.title))

		span_links = soup.findAll("span", "link")
		
		if len(span_links)==0:
			self.links.append((self.getIndexLink(), self.title))
		else:
			for span in span_links:
				chapter_link = span.a['href']
				chapter_name = span.a.string
				self.links.append((chapter_link, chapter_name))
			
		#self.index = self.cleanUp(soup)
			
	def cleanUp(self, soup):
		body = soup.html.body
		del(body['onload'])
					
					
		rm_list = soup.findAll(name='div', attrs={'id': 'bott-header',})
		[obj.extract() for obj in rm_list]
		rm_list = soup.findAll(name='div', attrs={'id': 'top-header',})
		[obj.extract() for obj in rm_list]
		
		rm_list = soup.findAll(name='h2', attrs={'class': 's-auth',})
		[obj.extract() for obj in rm_list]

		rm_list = soup.findAll(name='h3', attrs={'class': 'end',})
		[obj.extract() for obj in rm_list]
		
		rm_list = soup.findAll(name='h4', attrs={'class': 'copy',})
		[obj.extract() for obj in rm_list]

		rm_list = soup.findAll(name='span', attrs={'class': 'conTag'})
		[obj.extract() for obj in rm_list]
		
		rm_list = soup.findAll(name='span', attrs={'class': 'pager'})
		[obj.extract() for obj in rm_list]
		
		# remove date posted 
		rm_list = soup.findAll(name='div', attrs={'class': 'date'})
		[obj.extract() for obj in rm_list]

		# remove comment / blog section at last section
		rm_list = soup.findAll(name='p', attrs={'class': 'c'})
		[obj.extract() for obj in rm_list]
		##
		rm_list = soup.findAll(name='h5', attrs={'class': 'c'})
		[obj.extract() for obj in rm_list]

		# remove all br
		rm_list = soup.findAll(name='br')
		[obj.extract() for obj in rm_list]
		
		# remove extra link tags
		rm_list = soup.findAll(name='link', attrs={'rel': 'home'})
		[obj.extract() for obj in rm_list]
		rm_list = soup.findAll(name='link', attrs={'rel': 'index'})
		[obj.extract() for obj in rm_list]
		rm_list = soup.findAll(name='link', attrs={'rel': 'next'})
		[obj.extract() for obj in rm_list]
		
		rm_list = soup.findAll(name='meta')
		[obj.extract() for obj in rm_list]
		rm_list = soup.findAll(name='script')
		[obj.extract() for obj in rm_list]
		rm_list = soup.findAll(name='style')
		[obj.extract() for obj in rm_list]
		rm_list = soup.findAll(name='form')
		[obj.extract() for obj in rm_list]

		http_re = re.compile(r'http://')
		rm_list = soup.findAll(name='a', href = http_re)
		for obj in rm_list:
			obj['href'] = "#"
		
		return soup
					
	def getPageLinks(self, soup):
		pages = soup.findAll("span", "pager")
		if len(pages)==0:
			return []
		links = pages[0].findAll("a")[:-1]  # find all <a> except last <a> (next)
		
		return [a["href"] for a in links] 
		
	def getPages(self):
		#print "Chapters = %d" % len(self.links)
		if len(self.links)==1:
			link, title = self.links[0]
			content = self.getContent(link)
			page = "1"
			soup = BeautifulSoup(content)
			pages = self.getPageLinks(soup)
			chapter_id = str(self.story_id)
			yield (title, self.cleanUp(soup), chapter_id, page)
			for i in range(len(pages)):
				page = "%d" % (i+2)
				content = self.getContent(pages[i])
				soup = BeautifulSoup(content)
				yield (title, self.cleanUp(soup), chapter_id, page)
		else:
			for link, title in self.links:
				story_id, chapter_id = parse_link(link)
				content = self.getContent(link)
				soup = BeautifulSoup(content)
				pages = self.getPageLinks(soup)
				if len(pages):
					page = "1"
				else:
					page = ""
				yield (title, self.cleanUp(soup), chapter_id, page)
				for i in range(len(pages)):
					page = "%d" % (i+2)
					content = self.getContent(pages[i])
					soup = BeautifulSoup(content)
					yield (title, self.cleanUp(soup), chapter_id, page)
				
	def test(self):
		
		self.parseIndex()
		
		for link, name in self.links:
			print "%s %s [%s]" % (name, link, )
		
		
def test_main():
	logging.basicConfig(filename='SOLBook.log', level=logging.DEBUG)
	
	obj = SOLStory(56030);
	
	#obj.test()
		
	print "title: %s" % obj.title
	print "author: %s" % obj.author

	story_id = obj.story_id
	for (title, soup, chapter_id, page) in obj.getPages():
		print "%s (%s, %s, %s)" % (title, story_id, chapter_id, page)
		
if __name__ == "__main__":
	import sys
	sys.exit(test_main())

		
		
		
	
	
	