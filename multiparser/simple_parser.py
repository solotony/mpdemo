'''
    ____            _           _____
   / ___|    ___   | |   ___   |_   _|   ___    _ __    _   _
   \___ \   / _ \  | |  / _ \    | |    / _ \  | '_ \  | | | |
    ___) | | (_) | | | | (_) |   | |   | (_) | | | | | | |_| |
   |____/   \___/  |_|  \___/    |_|    \___/  |_| |_|  \__, |
   2020 (c) SoloTony.com                                |___/
   v 0.0.1 multi parser
'''

from typing import List
from socket import gaierror
from .base import BaseParser, Link, ProxyData, ParserException, format_proxy
from .simple import SimpleHistory, SimpleQueue
import requests
import logging
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError
import brotli

from .base import BaseParser, Link, ProxyData, ParserException
from .simple import SimpleHistory, SimpleQueue
from django.conf import settings
from requests.adapters import HTTPAdapter
requests.adapters.DEFAULT_RETRIES = 30

class SimpleParser(BaseParser):
    def __init__(self, base_url, virtual_display=False, proxy:ProxyData=None):
        super().__init__(base_url, virtual_display, proxy)
        self._base_url = base_url
        self._history = SimpleHistory()
        self._queue = SimpleQueue()
        self._session = None
        self._result = None
        self._status_code = 0
        self._proxy = None
        if proxy:
            if proxy.type == 'https':
                self._proxy = ProxyData(type='http', ip=proxy.ip, port=proxy.port, auth=proxy.auth)
            else:
                self._proxy = proxy

            logging.info("proxy used: {}".format(format_proxy(self._proxy)))

    def _start_session(self):
        self._session = requests.session()
        if not self._session:
            raise ParserException("requests.session failed")

        if self._proxy:
            self._session.proxies.update({
                "https": format_proxy(self._proxy),
                "http": format_proxy(self._proxy),
            })

    def mozilla_headers(self):
        return {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'max-age=0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36 OPR/71.0.3770.284',
        }

    def http_get_text(self, url, referrer)->[str, None]:
        self._session.headers.update(self.mozilla_headers())
        self._session.headers.update({'referer': referrer})
        try:
            self._result = self._session.get(url, timeout=(settings.REQUESTS_CONNECTION_TIMEOUT, settings.REQUESTS_DATA_TIMEOUT))
            if not self._result:
                self._status_code = 599
                logging.error('URL failed no result at [{}] '.format(url))
                return None
            self._status_code = self._result.status_code
            if self._status_code != 200:
                logging.error('URL failed status code=[{}] at [{}] '.format(self._status_code, url))
                return None
            result_text = self._result.text
            return result_text
        except ConnectionError as e:
            self._status_code = 599
            logging.error('ConnectionError at [{}] {}'.format(url, e))
            return None
        except gaierror as e:
            self._status_code = 599
            logging.error('socket.gaierror at [{}] {}'.format(url, e))
            return None


    def http_get(self, url, referrer, encoding=None)->[BeautifulSoup, None]:
        logging.info("http_get({}) {}".format(url, self.__class__))
        self._session.headers.update(self.mozilla_headers())
        self._session.headers.update({'referer': referrer})
        try:
            logging.info("{} {} {}".format(settings.REQUESTS_CONNECTION_TIMEOUT, settings.REQUESTS_DATA_TIMEOUT, self.__class__))
            self._result = self._session.get(url, timeout=(settings.REQUESTS_CONNECTION_TIMEOUT, settings.REQUESTS_DATA_TIMEOUT))
            if not self._result:
                self._status_code = 599
                logging.error('URL failed no result at [{}] '.format(url))
                return None
            self._status_code = self._result.status_code
            if self._status_code != 200:
                logging.error('URL failed status code=[{}] at [{}] '.format(self._status_code, url))
                return None
            if encoding:
                self._result.encoding = encoding
            soup = BeautifulSoup(self._result.text, 'html5lib')
            if not soup:
                logging.error('soup failed at [{}]'.format(url))
                return None
            return soup
        except ConnectionError as e:
            self._status_code = 599
            logging.error('ConnectionError at [{}] {}'.format(url, e))
            return None
        except gaierror as e:
            self._status_code = 599
            logging.error('socket.gaierror at [{}] {}'.format(url, e))
            return None

    def http_post(self, url, referrer, form_data=None)->[BeautifulSoup, None]:
        self._session.headers.update(self.mozilla_headers())
        self._session.headers.update({'referer': referrer})
        try:
            self._result = self._session.post(url, data=form_data, timeout=(settings.REQUESTS_CONNECTION_TIMEOUT, settings.REQUESTS_DATA_TIMEOUT))
            if not self._result:
                self._status_code = 599
                logging.error('URL failed no result at [{}] '.format(url))
                return None
            self._status_code = self._result.status_code
            if self._status_code != 200:
                logging.error('URL failed status code=[{}] at [{}] '.format(self._status_code, url))
                return None
            soup = BeautifulSoup(self._result.text, 'html5lib')
            if not soup:
                logging.error('soup failed at [{}]'.format(url))
                return None
            return soup
        except ConnectionError as e:
            self._status_code = 599
            logging.error('ConnectionError at [{}] {}'.format(url, e))
            return None
        except gaierror as e:
            self._status_code = 599
            logging.error('socket.gaierror at [{}] {}'.format(url, e))
            return None

    def http_last_status(self):
        return self._status_code

    def __enter__(self):
        self._start_session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            raise

    def __str__(self):
        return('{}({})'.format(self.__class__.__name__, self._base_url))


    def parse_products(self, links:[Link, List[Link]], fields: set) -> [dict, None]:
        logging.info('parse_products')
        if type(links) != list:
            links = [links]
        results = dict()
        for link in links:
            result = self.parse_product(link, fields)
            if result:
                results[link] = result
        return results
