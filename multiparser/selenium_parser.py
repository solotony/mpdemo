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
import requests
import logging
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from time import time, sleep
from django.conf import settings

from .base import BaseParser, Link, ProxyData, ParserException, format_proxy
from .simple import SimpleHistory, SimpleQueue
from base64 import b64encode

#from pyvirtualdisplay import Display
#display = Display(visible=0, size=(1280, 1024))
#display.start()


class SeleniumParser(BaseParser):

    def __init__(self, base_url=None, virtual_display=False, proxy:ProxyData=None):
        super().__init__(base_url, virtual_display, proxy)
        self._base_url = base_url
        self._history = SimpleHistory()
        self._queue = SimpleQueue()
        self._driver = None
        self._display = None
        self._last_status = None
        self._skip_base_url = False

    def __enter__(self):
        if self._virtual_display:
            from pyvirtualdisplay import Display
            self._display = Display(visible=0, size=(1920, 1080))
            self._display.start()

        options = None
        if self._proxy and self._proxy.auth:
            from seleniumwire import webdriver
            fp = webdriver.FirefoxProfile()
            if self._proxy.type == 'https':
                logging.info('set proxy {}'.format(str(self._proxy)))
                options = {
                    'proxy': {
                        'http': format_proxy(self._proxy),
                        'https': format_proxy(self._proxy),
                        'no_proxy': 'localhost,127.0.0.1'
                    }
                }
            elif self._proxy.type == 'socks4':
                logging.info('set proxy {}'.format(str(self._proxy)))
                options = {
                    'proxy': {
                        'http': format_proxy(self._proxy),
                        'https': format_proxy(self._proxy),
                        'no_proxy': 'localhost,127.0.0.1'
                    }
                }
            elif self._proxy.type == 'socks5':
                logging.info('set proxy {}'.format(str(self._proxy)))
                options = {
                    'proxy': {
                        'http': format_proxy(self._proxy),
                        'https': format_proxy(self._proxy),
                        'no_proxy': 'localhost,127.0.0.1'
                    }
                }
            fp.set_preference("http.response.timeout", 30)
            fp.set_preference("dom.max_script_run_time", 30)
            self._driver = webdriver.Firefox(firefox_profile=fp, seleniumwire_options=options)
        elif self._proxy:
            from selenium import webdriver
            fp = webdriver.FirefoxProfile()
            if self._proxy.type == 'https':
                logging.info('set proxy {}'.format(str(self._proxy)))
                fp.set_preference("network.proxy.type", 1)
                fp.set_preference("network.proxy.http", self._proxy.ip)
                fp.set_preference("network.proxy.http_port", self._proxy.port)
                fp.set_preference("network.proxy.ssl", self._proxy.ip)
                fp.set_preference("network.proxy.ssl_port", self._proxy.port)
                fp.update_preferences()
            elif self._proxy.type == 'socks4':
                logging.info('set proxy {}'.format(str(self._proxy)))
                fp.set_preference("network.proxy.type", 1)
                fp.set_preference("network.proxy.socks", self._proxy.ip)
                fp.set_preference("network.proxy.socks_port", self._proxy.port)
                fp.set_preference("network.proxy.socks_version", 4)
                fp.update_preferences()
            elif self._proxy.type == 'socks5':
                logging.info('set proxy {}'.format(str(self._proxy)))
                fp.set_preference("network.proxy.type", 1)
                fp.set_preference("network.proxy.socks", self._proxy.ip)
                fp.set_preference("network.proxy.socks_port", self._proxy.port)
                fp.set_preference("network.proxy.socks_version", 5)
                fp.update_preferences()
            fp.set_preference("http.response.timeout", 30)
            fp.set_preference("dom.max_script_run_time", 30)
            self._driver = webdriver.Firefox(firefox_profile=fp)
        else:
            from selenium import webdriver
            fp = webdriver.FirefoxProfile()
            fp.set_preference("http.response.timeout", 30)
            fp.set_preference("dom.max_script_run_time", 30)
            self._driver = webdriver.Firefox(firefox_profile=fp)

        self._driver.set_page_load_timeout(60)
        self._driver.implicitly_wait(30)
        self._driver.maximize_window()

        if not self._skip_base_url:
            root_url = self.base_url()
            soup = self.http_get(root_url, root_url)
            if not soup:
                soup = self.http_get(root_url, root_url)
                if not soup:
                    soup = self.http_get(root_url, root_url)
                    if not soup:
                        s = 'soup 3times failed at [{}]'.format(root_url)
                        logging.error(s)

                        raise ParserException(s)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._driver.close()
        if self._display:
            self._display.stop()
        if exc_val:
            logging.error(exc_val)

    def http_get_n(self, n, url, referrer) -> [BeautifulSoup, None]:
        if n < 0: n = 1
        if n > 9: n = 9
        while n>0:
            soup = self.http_get(url, referrer)
            if soup: return soup
        return None

    def http_get(self, url, referrer, encoding=None)->[BeautifulSoup, None]:
        try:
            res = self._driver.get(url)
            self.sleep(5)
            content = self._driver.execute_script("return document.body.outerHTML")
            soup = BeautifulSoup(content, 'html5lib')
            if not soup:
                logging.error('soup failed at [{}]'.format(url))
                if settings.SELENIUM_SAVE_SCREENSHOT_ON_ERROR:
                    self._driver.save_screenshot('logs/scr-err-' + str(time()).replace('.','-') + '.png')
                self._last_status = 597
                return None
            self._last_status = 200
            self._driver.save_screenshot('logs/scr-ok-' + str(time()).replace('.', '-') + '.png')
            return soup
        except TimeoutException as e:
            logging.error('selenium TimeoutException at [{}] {}'.format(url, str(e)))
            self._last_status = 598
            if settings.SELENIUM_SAVE_SCREENSHOT_ON_ERROR:
                self._driver.save_screenshot('scr-' + str(time()).replace('.','-') + '.png')
            return None
        except WebDriverException as e:
            logging.error('selenium WebDriverException at [{}] {}'.format(url, str(e)))
            self._last_status = 599
            if settings.SELENIUM_SAVE_SCREENSHOT_ON_ERROR:
                self._driver.save_screenshot('scr-' + str(time()).replace('.','-') + '.png')
            return None

    def http_last_status(self):
        return self._last_status

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

