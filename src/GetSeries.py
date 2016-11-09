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
import argparse

from GetBook import makebook


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


def main():
    # import sys

    parser = argparse.ArgumentParser(
        description="Process series page and download each story")
    parser.add_argument('url', metavar='url', type=str,
                        help="url of the page to parse")
    parser.add_argument('-u', '--user', metavar='username',
                        type=str, dest='user',
                        help='username to use when authenticating')
    parser.add_argument('-p', '--pass', metavar='password',
                        type=str, dest='passwd',
                        help='password to use when authenticating')

    args = parser.parse_args()

    # set default that we do not want to display
    if args.user:
        user = args.user
    else:
        user = 'blueboy88'

    if args.passwd:
        passwd = args.passwd
    else:
        passwd = 'vomisa'

    content = get_series_page(args.url)
    soup = BeautifulSoup(content)

    regex = re.compile('/s/([0-9]+)/.*')
    links = soup.findAll('a', href=regex)

    stories = [link['href'].split('/')[2] for link in links]

    base_path = os.path.basename(args.url)

    current_dir = os.getcwd()
    if not os.path.isdir(os.path.join(current_dir, base_path)):
        os.mkdir(base_path)

    os.chdir(base_path)

    count = len(stories)
    cur = 1
    for sid in stories:
        print "Downloading story {} of {}".format(cur, count)
        makebook(int(sid), user, passwd, 'http://storiesonline.net',
                 prefix="{} - ".format(cur))
        cur += 1

    os.chdir(current_dir)
if __name__ == "__main__":
    import sys
    sys.exit(main())
