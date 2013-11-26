import argparse, logging

import os

from SOLBook import SOLStory
from ebook import EPub, XHTMLFile
from mkcoverpg import MakeCoverPageStr

def bar(cur, count, symbol="#"):
	done_n = (20 * cur) / count
	
	done = symbol*done_n
	left = ' ' * (20 - done_n)
	
	percent = cur * 100 / count
	
	return "[%s] %d%%" % (done+left, percent)
	

def makebook(storyid):
	b = SOLStory(storyid)
	e = EPub(b.title, b.author, "storiesonline.net/s/" + str(b.story_id))
	logging.debug("storyid = %s (%s)"% (b.story_id, e.filename))
	
	basedir = os.path.dirname(os.path.abspath(__file__))
	logo = os.path.join(basedir, "data", "SOL-Mini-Logo.jpg")
	# add cover FIRST, very important to add it FIRST
	cover = MakeCoverPageStr(b.title, b.author, "storiesonline.net", logo)
	e.addCoverImage(cover)

	cwd = os.path.dirname(os.path.abspath(__file__))
	style = os.path.join(basedir, "data", "style.css")
	e.addStyle(os.path.join(cwd, style))
	
	count = b.chapter_count
	cur = 1
	for (title, soup, chapter_id, page) in b.getPages():
		logging.debug("adding (%d/%d) %s  [%s] %s" % (cur, count, title, chapter_id, page))
		print "\r", e.filename, "  ", bar(cur, count), "(%d/%d)" % (cur, count),
		
		x = XHTMLFile()
		x.headers.append(("link", None, {"rel": "stylesheet", "type": "text/css", "href": "../Styles/style.css"}))
		x.title = title
		if page:
			x.part = page
			x.title += ' Part ' + page
		else:
			cur += 1
		x.id = "c" + chapter_id
		x.content = soup.prettify()
		e.addChapter(x)
	e.close()	
	print "\n",

def main():
	parser = argparse.ArgumentParser(description='Process story ids and generate epubs from SOL.')
	parser.add_argument('ids', metavar='id', type=int, nargs='+',
						help='a story id to generate epub from')
	parser.add_argument('-D', '--debug', action='store_const',
						const=logging.DEBUG, default=logging.WARNING,
						help='enable debug mode')
	parser.add_argument('-f', '--log-file',
						default='logfile.txt',
						help='filename of log file (default: "logfile.txt")')
	args = parser.parse_args()

	logging.basicConfig(filename=args.log_file, format='%(levelname)s:%(message)s', level=args.debug)
	
	for id in args.ids:
		makebook(id)

if __name__ == "__main__":
	import sys
	sys.exit(main())
