#!/usr/bin/env python

__all__ = ['search']

import os
import random
import sys
import time
from http.cookiejar import LWPCookieJar
from urllib.request import Request, urlopen
from urllib.parse import quote_plus, urlparse, parse_qs
from bs4 import BeautifulSoup

# URL templates to make Google searches.
url_home = "https://www.google.com/"
url_search = "https://www.google.com/search?hl=cn&q=%(query)s&btnG=Google+Search&tbs=%(tbs)s&safe=%(safe)s"
url_next_page = "https://www.google.com/search?hl=cn&q=%(query)s&start=%(start)d&tbs=%(tbs)s&safe=%(safe)s"
url_search_num = "https://www.google.com/search?hl=cn&q=%(query)s&num=%(num)d&btnG=Google+Search&tbs=%(tbs)s&safe=%(safe)s"
url_next_page_num = "https://www.google.com/search?hl=cn&q=%(query)s&num=%(num)d&start=%(start)d&tbs=%(tbs)s&safe=%(safe)s"

home_folder = os.getenv('HOME')
if not home_folder:
    home_folder = os.getenv('USERHOME')
    if not home_folder:
        home_folder = '.'   # Use the current folder on error.
cookie_jar = LWPCookieJar(os.path.join(home_folder, '.google-cookie'))
try:
    cookie_jar.load()
except Exception:
    pass

# Default user agent, unless instructed by the user to change it.
USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)'

# Load the list of valid user agents from the install folder.
install_folder = os.path.abspath(os.path.split(__file__)[0])
user_agents_file = os.path.join(install_folder, 'user_agents.txt')
try:
    with open('user_agents.txt') as fp:
        user_agents_list = [_.strip() for _ in fp.readlines()]
except Exception:
    user_agents_list = [USER_AGENT]


def get_random_user_agent():
    return random.choice(user_agents_list)

def get_page(url, user_agent=None):
    if user_agent is None:
        user_agent = USER_AGENT
    try:
        request = Request(url)
        request.add_header('User-Agent', USER_AGENT)
        cookie_jar.add_cookie_header(request)
        response = urlopen(request)
        cookie_jar.extract_cookies(response, request)
        html = response.read()
        response.close()
        cookie_jar.save()
        return html
    except Exception:
        pass
    return None

def filter_result(link):
    try:
        o = urlparse(link, 'http')
        if o.netloc and 'google' not in o.netloc:
            return o.netloc
            # return link

        if link.startswith('/url?'):
            link = parse_qs(o.query)['q'][0]
            o = urlparse(link, 'http')
            if o.netloc and 'google' not in o.netloc:
                return o.netloc
                # return link

    except Exception:
        pass
    return None

def search(query, tbs='0', safe='off', num=10, start=0,
           stop=None, pause=2.0, only_standard=False, extra_params={}, tpe='', user_agent=None):
    hashes = set()
    query = quote_plus(query)

    # Check extra_params for overlapping
    for builtin_param in ('hl', 'q', 'btnG', 'tbs', 'safe'):
        if builtin_param in extra_params.keys():
            raise ValueError(
                'GET parameter "%s" is overlapping with \
                the built-in GET parameter',
                builtin_param
            )

    get_page(url_home % vars())

    if start:
        if num == 10:
            url = url_next_page % vars()
        else:
            url = url_next_page_num % vars()
    else:
        if num == 10:
            url = url_search % vars()
        else:
            url = url_search_num % vars()

    while not stop or start < stop:
        try:
            iter_extra_params = extra_params.iteritems()
        except AttributeError:
            iter_extra_params = extra_params.items()
        for k, v in iter_extra_params:
            url += url + ('&%s=%s' % (k, v))

        time.sleep(pause)
        html = get_page(url)
        soup = BeautifulSoup(html, 'html.parser')
        anchors = soup.find(id='search').findAll('a')
        for a in anchors:
            if only_standard and (
                    not a.parent or a.parent.name.lower() != "h3"):
                continue

            try:
                link = a['href']
            except KeyError:
                continue

            link = filter_result(link)
            if not link:
                continue

            h = hash(link)
            if h in hashes:
                continue
            hashes.add(h)
            yield link

        # End if there are no more results.
        if not soup.find(id='nav'):
            break

        # Prepare the URL for the next request.
        start += num
        if num == 10:
            url = url_next_page % vars()
        else:
            url = url_next_page_num % vars()