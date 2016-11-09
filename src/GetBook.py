#!/usr/bin/env python

"""
create .epub ebooks from a list of story ids
"""

import argparse
import logging


import os


from SOLBook import SOLStory
from ebook import EPub, XHTMLFile
from mkcoverpg import MakeCoverPageStr
from conutils import getTerminalSize

from BeautifulSoup import Tag
from os.path import basename
import requests

from fileutils import get_base_parent_path


def pbar(cur, count, max_width=28, symbol="#"):
    """
    print a progress bar
    """
    log_str = "bar(%d, %d, max_width=%d, symbol=%s" % \
        (cur, count, max_width, symbol)
    logging.debug(log_str)
    max_bar_w = max_width - 9
    # 9 = 5 (for 100%) +  3 (bracket & spaces) + 1 pad to prevent wrapping

    done_n = (max_bar_w * cur) / count

    done = symbol*done_n
    left = ' ' * (max_bar_w - done_n)

    percent = cur * 100 / count

    return "[%s] %4d%%" % (done+left, percent)


def full_justify(leftstr, rightstr):
    """
    pad with spaces between leftstr and rightstr so rightstr is right-justified
    """
    width, dummy = getTerminalSize()  # pylint: disable-msg=W0633
    str_w = len(leftstr) + len(rightstr)
    if str_w < width:
        padding = (width - 2) - str_w
        return leftstr + (" " * padding) + rightstr
    else:
        dim = width - len(rightstr) - 5
        return leftstr[:dim] + (leftstr[dim:] and '...') + rightstr


def download_image(imgurl, cookies):
    """
    download an image given its url and return it as string
    """
    return requests.get(imgurl, cookies=cookies)


def process_images(epub, soup, cookies):
    """
    download all the images found in IMG tags inside soup and
    change all the IMG tags to use local copy of the images
    """

    images = soup.findAll('img')
    for img in images:
        a_tag = Tag(soup, 'img')
        if 'alt' in img:
            a_tag['alt'] = img['alt']
        if 'title' in img:
            a_tag['title'] = img['title']
        src = img['src']
        res = download_image(src, cookies)
        a_tag['src'] = epub.add_image(basename(src), res.content)
        img.replaceWith(a_tag)


def make_xhtml(title, chapter_id, content, page=None):
    """
    return an XHTMLFile object
    """
    xhtml = XHTMLFile()
    xhtml.headers.append(("link", None, {"rel": "stylesheet",
                                         "type": "text/css",
                                         "href": "../Styles/style.css"}))
    xhtml.title = title
    if page:
        xhtml.part = page
        xhtml.title += ' Part ' + page
    xhtml.c_id = "c" + chapter_id
    xhtml.content = content.prettify()
    return xhtml


def get_story(story_id, user, passwd, url):
    """
    return a SOLStory object
    """
    story = SOLStory(story_id, user, passwd, url)
    if story.title.startswith("Welcome to the Web-Based Configurator"):
        raise Exception("Got modem-router no dsl connection page")
    return story


def make_cover(base_dir, title, author, url):
    """
    make a cover image from the title, author, and url, using SOL logo
    """
    logo = os.path.join(base_dir, "data", "SOL-Mini-Logo.jpg")
    # add cover FIRST, very important to add it FIRST
    site = url.split(r'/')[2]
    return MakeCoverPageStr(title, author, site, logo)


def make_epub(story, url, prefix=""):
    """
    initialize an EPub object with story (filename, title, autor),
    cover, and css style
    """
    # basedir = os.path.dirname(os.path.abspath(__file__))
    basedir = get_base_parent_path()
    epub = EPub(story.title, story.author, url[8:] + str(story.story_id),
                prefix=prefix)
    cover = make_cover(basedir, story.title, story.author, url)
    epub.add_cover_image(cover)
    style_path = os.path.join(basedir, "data", "style.css")
    epub.add_style(os.path.join(basedir, style_path))
    return epub


def makebook(storyid, user, passwd, url, prefix=""):
    """
    parse a url and make an ebook from the story
    """
    if url:
        if not url.startswith('http://'):
            url = 'http://' + url

    story = get_story(storyid, user, passwd, url)

    epub = make_epub(story, url, prefix=prefix)

    log_str = "storyid = %s (%s)" % (story.story_id, epub.filename)
    logging.debug(log_str)

    count = story.chapter_count
    cur = 1
    last_title = ""
    for (title, soup, chapter_id, page) in story.get_pages():
        log_str = "adding (%d/%d) %s  [%s] %s" % \
            (cur, count, title, chapter_id, page)
        logging.debug(log_str)

        barstr = " %s (%d/%d)" % (pbar(cur, count), cur, count)
        print "\r", full_justify(epub.filename, barstr),

        if last_title != title:
            cur += 1
            last_title = title
        process_images(epub, soup, story.cookies)
        epub.add_chapter(make_xhtml(title, chapter_id, soup, page))
    epub.close()
    print "\r\n",


def print_missing_data():
    """
    print that the data folder must exist, and where
    """
    print ".%s%s folder must exists" % (os.path.sep, 'data')
    print "it must contain SOL-Mini-Logo.jpg and style.css."


def check_data_folder():
    """
    check for data folder, where the css and cover logo should be
    """
    basedir = get_base_parent_path()
    if not os.path.isdir(os.path.join(basedir, 'data')):
        print_missing_data()
        return -1

    if not os.path.exists(os.path.join(basedir,
                                       'data', 'SOL-Mini-Logo.jpg')):
        print "Cover page logo image not found in data folder."
        print_missing_data()
        return -2

    if not os.path.exists(os.path.join(basedir, 'data', 'style.css')):
        print "CSS stylesheet not found in data folder."
        print_missing_data()
        return -3

    return 0


def main():
    """
    main function
    read list of id from command-line arguments and parse into ebooks
    """

    parser = argparse.ArgumentParser(
        description='Process story ids and generate epubs from SOL.')
    parser.add_argument('ids', metavar='id', type=str, nargs='+',
                        help='a story id to generate epub from')
    parser.add_argument('-D', '--debug', action='store_const',
                        const=logging.DEBUG, default=logging.WARNING,
                        help='enable debug mode')
    parser.add_argument('-f', '--log-file',
                        default='logfile.txt',
                        help='filename of log file (default: "logfile.txt")')
    parser.add_argument('-u', '--user', metavar='username',
                        type=str, dest='user',
                        help='username to use when authenticating')
    parser.add_argument('-p', '--pass', metavar='password',
                        type=str, dest='passwd',
                        help='password to use when authenticating')
    parser.add_argument('-s' '--site', metavar='url', type=str, dest='url',
                        default='storiesonline.net',
                        help='the url of the stories site ' +
                        '(finestories.com/storiesonline.net)')
    args = parser.parse_args()

    logging.basicConfig(filename=args.log_file,
                        format='%(levelname)s:%(message)s', level=args.debug)

    # check if data folder exists
    chk_res = check_data_folder()
    if chk_res != 0:
        return chk_res

    if args.user:
        user = args.user
    else:
        user = 'blueboy88'  # becomes 'azuer.dragon.88@gmail.com' by 1/1/2015
    if args.passwd:
        passwd = args.passwd
    else:
        passwd = 'vomisa'

    url = args.url
    if not url.startswith('http://'):
        url = 'http://' + url.strip("/")
    url_str = "%s/s/" % url

    for sid in args.ids:
        if sid.startswith(url_str):
            sid = sid[len(url_str):].split('/')[0]
        m_id = int(sid)
        makebook(m_id, user, passwd, url)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
