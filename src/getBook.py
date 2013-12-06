import argparse, logging

import os

from SOLBook import SOLStory
from ebook import EPub, XHTMLFile
from mkcoverpg import MakeCoverPageStr
from conutils import getTerminalSize

def bar(cur, count, max_width=28, symbol="#"):
	logging.debug("bar(%d, %d, max_width=%d, symbol=%s" % (cur, count, max_width, symbol))
	max_bar_w = max_width - 8 # 8 = 4 (for 100%) +  3 (bracket & spaces) + 1 pad to prevent wrapping
	done_n = (max_bar_w * cur) / count
	
	done = symbol*done_n
	left = ' ' * (max_bar_w - done_n)
	
	percent = cur * 100 / count
	
	return "[%s] %3d%%" % (done+left, percent)
	
def full_justify(leftstr, rightstr):
	w, h = getTerminalSize()
	str_w = len(leftstr) + len(rightstr)
	if  str_w < w:
		padding = (w - 1) - str_w
		return leftstr + (" " * padding) + rightstr
	else:
		d = w - len(rightstr) - 4
		return leftstr[:d] + (leftstr[d:] and '...') + rightstr
		

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
	last_title = ""
	for (title, soup, chapter_id, page) in b.getPages():
		logging.debug("adding (%d/%d) %s  [%s] %s" % (cur, count, title, chapter_id, page))

		barstr = " %s (%d/%d)" % (bar(cur, count), cur, count)
		print "\r", full_justify(e.filename, barstr),
		
		x = XHTMLFile()
		x.headers.append(("link", None, {"rel": "stylesheet", "type": "text/css", "href": "../Styles/style.css"}))
		x.title = title
		if page:
			x.part = page
			x.title += ' Part ' + page
		if last_title<>title:
			cur += 1
			last_title = title
		x.id = "c" + chapter_id
		x.content = soup.prettify()
		e.addChapter(x)
	e.close()	
	print "\r",

def print_missing_data():
	print ".%s%s folder must exists" % (os.path.sep, 'data')
	print "it must contain SOL-Mini-Logo.jpg and style.css."

def check_data_folder():
	if not os.path.isdir(os.path.join(os.getcwd(), 'data')):
		print_missing_data()
		return -1
		
	if not os.path.exists(os.path.join(os.getcwd(), 'data', 'SOL-Mini-Logo.jpg')):
		print "Cover page logo image not found in data folder."
		print_missing_data()
		return -2
		
	if not os.path.exists(os.path.join(os.getcwd(), 'data', 'style.css')):
		print "CSS stylesheet not found in data folder."
		print_missing_data()
		return -3
		
	return 0
	

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
	
	# check if data folder exists
	chk_res = check_data_folder()
	if (chk_res<>0):
		return chk_res
	
	for id in args.ids:
		makebook(id)
		
	return 0

if __name__ == "__main__":
	import sys
	sys.exit(main())
