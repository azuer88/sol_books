#!/usr/bin/env python
"""
class for reusing the saved cookies if it exists, log into SOL to get new
ones if none exists
"""
import os.path
import logging, pickle, urllib, requests

from fileutils import get_real_fname, get_base_parent_path

def make_headers():
    """
    return dict content-type header for logging in
    """
    return  {'Content-type': 'application/x-www-form-urlencoded'}


class SOLUser(object):
    """
    defines a user object used to retrieve cookies, or login if none exists
    """
    #cookie_file = os.path.join('data', 'cookies.dat')
    #username = ''
    #password = ''

    def __init__(self, user, password):
        self.username = user
        self.password = password
        basepath = get_base_parent_path()
        self.cookie_file = os.path.join(basepath, 'data', user, 'cookies.dat')


    def make_body(self):
        """
        create dict and return for logging with username and password
        """
        return urllib.urlencode({'theusername': self.username,
                                 'thepassword': self.password,
                                 'submit':'Login'})

    def get_cookies(self, url='http://storiesonline.net/login'):
        """
        Get stored cookies, or login and store return new cookies
        """
        if os.path.exists(self.cookie_file):
            logging.info('using cookie file - %s', self.cookie_file)
            with open(self.cookie_file, "r") as storage:
                cookies = pickle.load(storage)
            #f.close()
        else:
            logging.info('No cookie file found - trying to login instead.')
            headers = make_headers()
            body = self.make_body()

            result = requests.post(url, data=body, headers=headers,
                                   allow_redirects=False)
            # errorlogging.log(logging.DEBUG, "login status code: ", result.status_code)

            cookies = result.cookies

            with open(self.cookie_file, "w") as storage:
                pickle.dump(cookies, storage)
            #f.close()

        return cookies

