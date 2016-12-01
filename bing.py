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

url_home = "http://cn.bing.com/"
http://cn.bing.com/search?q=python+vars&go=Search&qs=n&form=QBRE&pq=python+vars&sc=6-11&sp=-1&sk=&cvid=D7984BD8E29343DCBA990E55E22EA286
url_search = "http://cn.bing.com/search?q=%(query)s&go=Search"
url_next_page = "https://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&start=%(start)d&tbs=%(tbs)s&safe=%(safe)s&tbm=%(tpe)s"
url_search_num = "https://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&num=%(num)d&btnG=Google+Search&tbs=%(tbs)s&safe=%(safe)s&tbm=%(tpe)s"
url_next_page_num = "https://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&num=%(num)d&start=%(start)d&tbs=%(tbs)s&safe=%(safe)s&tbm=%(tpe)s"

# Cookie jar. Stored at the user's home folder.
home_folder = os.getenv('HOME')
if not home_folder:
    home_folder = os.getenv('USERHOME')
    if not home_folder:
        home_folder = '.'   # Use the current folder on error.
cookie_jar = LWPCookieJar(os.path.join(home_folder, '.bing-cookie'))
try:
    cookie_jar.load()
except Exception:
    pass

USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)'

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
    request = Request(url)
    request.add_header('User-Agent', USER_AGENT)
    cookie_jar.add_cookie_header(request)
    response = urlopen(request)
    cookie_jar.extract_cookies(response, request)
    html = response.read()
    response.close()
    cookie_jar.save()
    return html


def filter_result(link):
    try:
        o = urlparse(link, 'http')
        if o.netloc and 'bing' not in o.netloc:
            return o.netloc
        if link.startswith('/url?'):
            link = parse_qs(o.query)['q'][0]
            o = urlparse(link, 'http')
            if o.netloc and 'bing' not in o.netloc:
                return o.netloc
    except Exception:
        pass
    return None




def search(query, tbs='0', safe='off', num=10, start=0,
           stop=None, pause=2.0, only_standard=False, extra_params={}, tpe='', user_agent=None):
    hashes = set()

    # Prepare the search string.
    query = quote_plus(query)

    for builtin_param in ('hl', 'q', 'btnG', 'tbs', 'safe', 'tbm'):
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

        try:  # Is it python<3?
            iter_extra_params = extra_params.iteritems()
        except AttributeError:  # Or python>3?
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

        if not soup.find(id='nav'):
            break

        start += num
        if num == 10:
            url = url_next_page % vars()
        else:
            url = url_next_page_num % vars()
