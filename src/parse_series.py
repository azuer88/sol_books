#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 14 18:11:20 2014

@author: azuer88

"""

from BeautifulSoup import BeautifulSoup
from urllib2 import Request, urlopen, URLError

import re
import os


def get_series_page(url):
    content = None
    req = Request(url)
    try:
      response = urlopen(req)
    except URLError as e:
      if hasattr(e, 'reason'):
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
        return None
      elif hasattr(e, 'code'):
        print 'The server could\'t fullfil the request.'
        print 'Code: ', e.code
        return None
      else:
        print 'reading page %s ...' % url
    content = response.read()
    response.close()

    return content

def main2():
    #url = sys.argv(1)
    regex = re.compile('/s/([0-9]+)/.*')

    with open(sys.argv[1]) as inp:
        content = inp.read()

    soup = BeautifulSoup(content)

    links = soup.findAll('a', href=regex)

    for link in links:
        print link['href'].split('/')[2],
        #print link.split('/')[2]

    #print links

def main():
    import sys

    #url = sys.argv(1)
    regex = re.compile('/s/([0-9]+)/.*')

    #content = os.popen('xsel').read()
    if len(sys.argv)==2:
         content = get_series_page(sys.argv[1])
    else:
         print "Needs url of series page."
         exit(1)


    soup = BeautifulSoup(content)
    #print soup.prettify()

    links = soup.findAll('a', href=regex)

    for link in links:
        print link['href'].split('/')[2],
        #print link.split('/')[2]

    #print links


if __name__ == "__main__":
    import sys
    sys.exit(main())
