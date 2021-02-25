'''
    ____            _           _____
   / ___|    ___   | |   ___   |_   _|   ___    _ __    _   _
   \___ \   / _ \  | |  / _ \    | |    / _ \  | '_ \  | | | |
    ___) | | (_) | | | | (_) |   | |   | (_) | | | | | | |_| |
   |____/   \___/  |_|  \___/    |_|    \___/  |_| |_|  \__, |
   2020 (c) SoloTony.com                                |___/
   v 0.0.1 duim24
'''

from ..simple_parser import SimpleParser
from ..base import Link, ProxyData
import logging
from typing import List
from time import time
import re

re_price = re.compile('[^0-9,.]')

class ParserDuim24Ru(SimpleParser):
    def __init__(self, base_url='https://www.duim24.ru'):
        super().__init__(base_url)

    def url(self, link: Link) -> str:
        return link.id

    def base_url(self) -> str:
        return self._base_url + '/'

    def build_initial_list(self)->bool:
        root = self.base_url()
        soup = self.http_get(root, root)
        if not soup:
            return False
        div_tag = soup.find('div', attrs={'class': 'main-links'})
        if not div_tag:
            logging.error('(1) div[class="main-links"] not found at [{}]'.format(root))
            return False
        a_tags = div_tag.findAll('a')
        if not a_tags:
            logging.error('(2) a not found at [{}]'.format(root))
            return False
        links = [Link(type='C', id=a.get('href')) for a in a_tags]
        self._queue.put(links)
        return True

    def parse_categories(self, links:[Link, List[Link]], fields: set, product_fields: set = None) -> [dict, None]:
        results = dict()
        if type(links) != list:
            links = [links]
        #print('links={}'.format(links))
        for link in links:
            result = self.parse_category(link, fields, product_fields)
            if result:
                results[link] = result
        return results

    def parse_category(self, link: Link, fields: set, product_fields: set = None) -> [dict, None]:
        logging.info('parse_category {}'.format(link))
        result = dict()
        if self.PARSED_TIME in fields:
            result[self.PARSED_TIME] = time()
        #print('link={}'.format(link))
        url = self.url(link)
        if self.PARSED_URL in fields:
            result[self.PARSED_URL] = url
        soup = self.http_get(url, self.base_url())
        if not soup:
            return
        div_tag = soup.find('div', attrs={'class': 'pager-bottom'})
        if not div_tag:
            logging.warning('(3) div[class="pager-bottom"] not found at [{}]'.format(url))
        else:
            a_tags = div_tag.findAll('a')
            if not a_tags:
                logging.warning('(4) a not found at [{}]'.format(url))
            result['pages'] = set()
            for a in a_tags:
                href = a.get('href')
                if href:
                    result['pages'].add(href.strip())

        div_tags = soup.findAll('div', attrs={'class': 'tovar-descript'})
        if not div_tags:
            logging.warning('(3) div[class="tovar-descript"] not found at [{}]'.format(url))
        else:
            result['products'] = dict()
            for div_tag in div_tags:
                a_tags = div_tag.findAll('a')
                if not a_tags:
                    logging.warning('(5) a not found at [{}]'.format(url))
                for a in a_tags:
                    href = a.get('href')
                    if href and href[:9]=='/catalog/':
                        result['products'][href.strip()] = dict()
        return result

    def walk_site(self, reset=False):
        '''
        Выполняет полный обход сайта.
        В парсер в идеале умеет сохранять свое состояние, - то есть он может быть прерван,
        а затем его выполнение будет продолжено. для
        '''

        categories_fields = {self.PARSED_TIME, self.PARSED_URL, self.FIELD_NAME, self.FIELD_PAGES, self.FIELD_PRODUCTS}
        categories_products_fields = {self.FIELD_URL}
        products_fields = {self.PARSED_TIME, self.PARSED_URL, self.FIELD_URL, self.FIELD_PRICE}

        if reset:
            self.build_initial_list()

        while self._queue.has(typ='C'):
            #print('1-1:', str(self._queue))
            links = self._queue.pop(typ='C', cnt=1)
            #print('1-1 links=', str(links)),
            #print('1-1:', str(self._queue))
            self._history.put(links)
            result = self.parse_categories(links, categories_fields, categories_products_fields)
            for link in result:
                if type(result[link]) == dict:
                    if 'products' in result[link]:
                        for url in result[link]['products']:
                            product_link = Link(type='P', id=url)
                            if product_link not in self._history and product_link not in self._queue:
                                self._queue.put(product_link)
                    if 'pages' in result[link]:
                        for url in result[link]['pages']:
                            page_link = Link(type='C', id=url)
                            if page_link not in self._history and page_link not in self._queue:
                                self._queue.put(page_link)

        while self._queue.has(typ='P'):
            links = self._queue.pop(typ='P', cnt=1)
            parsed = self.parse_products(links, products_fields)

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


    def parse_product(self, link: Link, fields: set) -> [dict, None]:
        logging.info('parse_product {}'.format(link))
        #print('parse_product {}'.format(link))
        # with open('products.txt', 'a', encoding='utf-8') as outfile:
        #     print(self.url(link), file=outfile)

        result = {x:None for x in fields} # результат должен содержать все требуемые параметры, даже если они не найдены

        url = self.url(link)
        soup = self.http_get(url, self.base_url())
        if self.PARSED_STATUS in fields:
            result[self.PARSED_STATUS] = self.http_last_status()
        if self.PARSED_PROXY in fields:
            result[self.PARSED_PROXY] = self.proxy_string()
        if self.PARSED_TIME in fields:
            result[self.PARSED_TIME] = time()
        if self.PARSED_URL in fields:
            result[self.PARSED_URL] = url

        if self.FIELD_NAME in fields:
            h1_tag = soup.find('h1', attrs={'itemprop': 'name'})
            if not h1_tag:
                logging.error('h1 not found in url=[{}]'.format(url))
            else:
                result[self.FIELD_NAME] = h1_tag.text.strip().replace(';', '.')
        if self.FIELD_ARTICUL in fields or self.FIELD_PRICE in fields:
            div_tag = soup.find('div', attrs={'class': 'popup-tobasket'})
            if not div_tag:
                logging.error('div.popup-tobasket not found url=[{}]'.format(url))
            else:
                if self.FIELD_ARTICUL in fields:
                    span_tag = soup.find('span', attrs={'itemprop': 'sku'})
                    if not span_tag:
                        logging.error('span.sku not found in url=[{}]'.format(url))
                    else:
                        result[self.FIELD_ARTICUL] = span_tag.text.strip().replace(';', '.')
                if self.FIELD_PRICE in fields:
                    span_tag = soup.find('span', attrs={'itemprop': 'price'})
                    if not span_tag:
                        logging.error('span.price not found in url=[{}]'.format(url))
                    else:
                        price = span_tag.get('content').strip()
                        price = re_price.sub('', price).replace(',','.')
                        try:
                            result[self.FIELD_PRICE] = float(price)
                        except ValueError:
                            pass


        return result

        # nav_tag = soup.find('nav', attrs={'class': 'breadcrumbs'})
        # if not nav_tag:
        #     logging.error('nav.breadcrumbs not found in [{}]'.format(s))
        # else:
        #     breadcrumbs = nav_tag.get_text(strip=True, separator=" ").replace(';', '.').replace(',', '.')
        #     breadcrumbs = '/'.join(breadcrumbs.split(' / ')[2:-1])
        #
        # div_tag = soup.find('div', attrs={'class': 'slider-for-cont'})
        # if not div_tag:
        #     logging.error('images not found in [{}]'.format(s))
        # else:
        #     images = [x.get('href') for x in div_tag.findAll('a')]
        #     images = ','.join(images)
        #
        # div_tag = soup.find('div', attrs={'class': 'item_tab_properties'})
        # if not div_tag:
        #     logging.error('properties not found in [{}]'.format(s))
        # else:
        #     options = []
        #     for ul_tag in div_tag.findAll('dl'):
        #         dt_tag = ul_tag.find('dt')
        #         dd_tag = ul_tag.find('dd')
        #         if dt_tag and dd_tag:
        #             options.append('{}:{}'.format(dt_tag.text.strip().replace(';', '.').replace(',', '.'),
        #                                           dd_tag.text.strip().replace(';', '.').replace(',', '.').replace(':',
        #                                                                                                           '.')))
        #     options = ','.join(options)
        #
        # table_tag = soup.find('table', attrs={'class': 'checkall-parent'})
        # if not table_tag:
        #     logging.error('files not found in [{}]'.format(s))
        # else:
        #     files = []
        #     for tr_tag in table_tag.findAll('tr'):
        #         td_tags = tr_tag.findAll('td')
        #         if td_tags and len(td_tags) >= 5:
        #             a_tag = td_tags[5].find('a')
        #             if a_tag:
        #                 files.append('{}:{}'.format(a_tag.get('href'),
        #                                             td_tags[2].text.strip().replace(';', '.').replace(',', '.').replace(':',
        #                                                                                                                 '.')))
        #     files = ','.join(files)

    #     '''
    #     Парсит список продуктов
    #
    #     Обязательные параметры
    #
    #     * product_ids -- список продуктов для парсинга
    #     * fields -- список собираемых полей
    #
    #     Возвращает dict вида
    #
    #     {
    #         id:{ field:value, field:value, field:value ...}, ...
    #     }
    #
    #     * Виртуальный метод.
    #     * Метод не должен поднимать исключений.
    #     '''
    #     return
    #

