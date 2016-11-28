#!/usr/bin/env python
"""
class for leeching a story given a story id
"""
#import os.path,
import htmllib
import logging
import re
import requests

from BeautifulSoup import BeautifulSoup  # removed Tag
from SOLUser import SOLUser

LINK_RE = re.compile(
    r'/(?P<url>(sex-)?s(tory)?)/(?P<story>\d+):' +
    r'(?P<chapter>\d+|i);?(?P<page>\d*)')


def parse_link(href):
    """
    parses a url into story and chapter components
    """
    result = LINK_RE.search(str(href))
    if result:
        story = result.group('story')
        chapter = result.group('chapter')
        return (story, chapter)
    else:
        return None


def unescape(in_string):
    """
    unescape a string
    """
    parser = htmllib.HTMLParser(None)
    parser.save_bgn()
    parser.feed(in_string)
    return parser.save_end()


def no_clean_up(soup):
    """
    debug clean_up, do nothing
    """
    return soup


def clean_up(soup):
    """
    removes extraneous html tags and formatting from the content 'soup'
    """
    body = soup.html.body
    del body['onload']

    rm_list = soup.findAll(name='div', attrs={'id': 'bott-header', })
    dummy = dummy = [obj.extract() for obj in rm_list]
    rm_list = soup.findAll(name='div', attrs={'id': 'top-header', })
    dummy = [obj.extract() for obj in rm_list]

    rm_list = soup.findAll(name='h2', attrs={'class': 's-auth', })
    dummy = [obj.extract() for obj in rm_list]

    rm_list = soup.findAll(name='h3', attrs={'class': 'end', })
    dummy = [obj.extract() for obj in rm_list]

    rm_list = soup.findAll(name='h4', attrs={'class': 'copy', })
    dummy = [obj.extract() for obj in rm_list]

    rm_list = soup.findAll(name='span', attrs={'class': 'conTag'})
    dummy = [obj.extract() for obj in rm_list]

    rm_list = soup.findAll(name='div', attrs={'class': 'pager'})
    dummy = [obj.extract() for obj in rm_list]
    rm_list = soup.findAll(name='span', attrs={'class': 'pager'})
    dummy = [obj.extract() for obj in rm_list]

    # remove date posted
    rm_list = soup.findAll(name='div', attrs={'class': 'date'})
    dummy = [obj.extract() for obj in rm_list]

    # remove <ul> bottNav
    rm_list = soup.findAll(name='ul', attrs={'class': 'bottNav'})
    dummy = [obj.extract() for obj in rm_list]

    # remove comment / blog section at last section
    rm_list = soup.findAll(name='p', attrs={'class': 'c'})
    dummy = [obj.extract() for obj in rm_list]

    # remove tweet div
    rm_list = soup.findAll(name='div', attrs={'class': 'r'})
    dummy = [obj.extract() for obj in rm_list]

    # remove voting div
    rm_list = soup.findAll(name='div', attrs={'class': 'vform'})
    dummy = [obj.extract() for obj in rm_list]

    # remove header section
    rm_list = soup.findAll(name='header')
    dummy = [obj.extract() for obj in rm_list]

    # remove view series div
    rm_list = soup.findAll(name='h4', attrs={'class': 'c', })
    dummy = [obj.extract() for obj in rm_list]

    ##
    rm_list = soup.findAll(name='h5', attrs={'class': 'c'})
    dummy = [obj.extract() for obj in rm_list]

    # remove all br
    rm_list = soup.findAll(name='br')
    dummy = [obj.extract() for obj in rm_list]

    # remove extra link tags
    rm_list = soup.findAll(name='link', attrs={'rel': 'home'})
    dummy = [obj.extract() for obj in rm_list]
    rm_list = soup.findAll(name='link', attrs={'rel': 'index'})
    dummy = [obj.extract() for obj in rm_list]
    rm_list = soup.findAll(name='link', attrs={'rel': 'next'})
    dummy = [obj.extract() for obj in rm_list]

    #rm_list = soup.findAll(name='meta')
    #dummy = [obj.extract() for obj in rm_list]
    rm_list = soup.findAll(name='script')
    dummy = [obj.extract() for obj in rm_list]
    rm_list = soup.findAll(name='style')
    dummy = [obj.extract() for obj in rm_list]
    rm_list = soup.findAll(name='form')
    dummy = [obj.extract() for obj in rm_list]

    http_re = re.compile(r'http://')
    rm_list = soup.findAll(name='a', href=http_re)
    for obj in rm_list:
        obj['href'] = "#"

    return soup


def get_page_links(soup):
    """
    parses the content 'soup' for the links to the pages
    and chapters, puts each one into `links` and returns the list
    """
    pages = soup.findAll("span", "pager")
    if len(pages) == 0:
        pages = soup.findAll("div", "pager")
    if len(pages) == 0:
        return []
    # print "pager", pages
    # find all <a> except last <a> (next)
    links = pages[0].findAll("a")[:-1]
    # print "links", links 
    return [a["href"] for a in links]


class SOLStory(object):
    """
    retrieves the pages of a story given a story id
    """
    base_url = 'http://storiesonline.net'

    @property
    def chapter_count(self):
        """
        returns the number of chapters
        """
        return len(self.links)

    def __init__(self, story_id, user, passwd, url='http://storiesonline.net'):
        log_msg = 'initializing story object (id: %d)' % story_id
        logging.debug(log_msg)
        self.base_url = url
        self.story_id = story_id
        #self.headers = None
        self.links = []
        self.title = ""
        self.author = ""

        self.clean_up = clean_up

        log_msg = 'creating user - %s - for logging in or cookies' % user
        user = SOLUser(user, passwd)
        self.cookies = user.get_cookies()

        self.parse_index()

    def get_content(self, page_url):
        """
        returns the content of the page_url
        """
        logging.debug('fetching URL = %s', page_url)
        tries = 4
        success = False

        target_url = self.base_url + page_url
        while (tries > 0) and (not success):
            try:
                response = requests.get(target_url, cookies=self.cookies)
                success = True
            except:  # pylint: disable-msg=W0702
            #requests.ConnectionError:
                tries -= 1
                print "ConnectionError... retrying (#%d)" % tries

        if not success:  # try one last time
            response = requests.get(target_url, cookies=self.cookies)

        logging.debug('response(%s|%s)',
                      response.status_code,
                      response.encoding)

        return response.text

    def get_index_link(self):
        """
        returns the url of the story's index given the story's id
        """
        return '/s/%s' % self.story_id

    def get_index_content(self):
        """
        returns the content of the index
        """
        url = self.get_index_link()

        return self.get_content(url)

    def parse_index(self):
        """
        parses the index of the story
        index is the page where all the links to the chapters are
        """
        content = self.get_index_content()

        soup = BeautifulSoup(content)

        title = soup.findAll('title')[0].string
        title = title.replace(" (Page 1) ", "")
        try:
            log_str = "title string: %s" % title
            logging.debug(log_str)
            author, dummy, title = title.partition(': ')
            log_str = "author: '%s' title: '%s'" % (author, title)
            logging.debug(log_str)
            title = unescape(title)
        except:  # pylint: disable-msg=W0702
            i = title.find(' by ')
            author = title[i+4]
            title = title[:i]

            reg_ex = re.compile(r'\s*\([^)]*\)')
            author = reg_ex.sub('', author)

        self.author = author
        self.title = title.replace(" (Page 1)", " ").strip()

        log_str = "(after normalize) author: '%s' title: '%s'" % \
            (self.author, self.title)
        logging.debug(log_str)

        #span_links = soup.findAll("span", "link")

        #if len(span_links)==0:
        #    self.links.append((self.get_index_link(), self.title))
        #else:
        #    for span in span_links:
        #        chapter_link = span.a['href']
        #        chapter_name = span.a.string
        #        self.links.append((chapter_link, chapter_name))

        idx_links = soup.find('div', id='index-list')
        if idx_links:
            links = idx_links.findAll('a')

            for link in links:
                chapter_link = link['href']
                chapter_name = link.string
                if chapter_link[-2:] == ':d':
                    continue
                self.links.append((chapter_link, chapter_name))
        else:
            self.links.append((self.get_index_link(), self.title))

        #self.index = clean_up(soup)

    def get_pages(self):
        """
        read the pages of the story
        read the pages of the story based on the contents of 'links',
        where 'links' contains the one entry for every page or chapter.
        """
        #print "Chapters = %d" % len(self.links)
        if len(self.links) == 1:
            link, title = self.links[0]
            content = self.get_content(link)
            page = "1"
            soup = BeautifulSoup(content)
            pages = get_page_links(soup)
            chapter_id = str(self.story_id)
            yield (title, self.clean_up(soup), chapter_id, page)
            for i in range(len(pages)):
                page = "%d" % (i+2)
                content = self.get_content(pages[i])
                soup = BeautifulSoup(content, fromEncoding="utf-8")
                yield (title, self.clean_up(soup), chapter_id, page)
        else:
            for link, title in self.links:
                #story_id, chapter_id = parse_link(link)
                chapter_list = parse_link(link)
                dummy, chapter_id = chapter_list  # pylint: disable-msg=W0633
                content = self.get_content(link)
                soup = BeautifulSoup(content)
                pages = get_page_links(soup)
                if len(pages):
                    page = "1"
                else:
                    page = ""
                yield (title, self.clean_up(soup), chapter_id, page)
                for i in range(len(pages)):
                    page = "%d" % (i+2)
                    content = self.get_content(pages[i])
                    soup = BeautifulSoup(content, fromEncoding="utf-8")
                    yield (title, self.clean_up(soup), chapter_id, page)

    def test(self):
        """
        test parse_index() method
        """
        self.parse_index()

        for link, name in self.links:
            print "%s %s [%s]" % (name, link, "")


def test_main():
    """
    test function
    test everything by loading/leeching one story
    """

    logging.basicConfig(filename='SOLBook.log', level=logging.DEBUG)

    obj = SOLStory(76043, 'azuer88', 'pass.1234')

    #obj.test()

    print "title: %s" % obj.title
    print "author: %s" % obj.author

    story_id = obj.story_id
    for (title, dummy, chapter_id, page) in obj.get_pages():
        print "%s (%s, %s, %s)" % (title, story_id, chapter_id, page)

if __name__ == "__main__":
    import sys
    sys.exit(test_main())
