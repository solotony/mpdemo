'''
    ____            _           _____
   / ___|    ___   | |   ___   |_   _|   ___    _ __    _   _
   \___ \   / _ \  | |  / _ \    | |    / _ \  | '_ \  | | | |
    ___) | | (_) | | | | (_) |   | |   | (_) | | | | | | |_| |
   |____/   \___/  |_|  \___/    |_|    \___/  |_| |_|  \__, |
   2020 (c) SoloTony.com                                |___/
   v 0.0.1 multi parser

для парсеров, выполняющих обход, текущее состояние хранится в очереди.
очередь может храниться например в базе данных, или в объекте, который
сохраняется/восстанавливается из pickle
'''

from collections import namedtuple
from typing import List
from time import sleep
import logging
import re
from bs4 import BeautifulSoup

#  тип 'Link' - это описание ссылки
#  type - тип ссылки ('C' сылка на категорию, 'G' сылка на страницу категории(для многостраничных),
#  'M' ссылка на главную стрницу, 'P' ссылка ана товар, 'S' ссылка на поисковую фразу, 'F' ссылка на фильтр)
#  id - это идентификатор. id может быть чем угодно - идентификатором, локальной ссылкой, полным URL,
#  поисковой фразой, набором фильтров.
#  преобразование URL

re_ip = re.compile('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')

Link = namedtuple('Link', 'type id')
ProxyData = namedtuple('Proxy', 'type ip port auth', defaults=(None,None,None,None))

def format_proxy(proxy:ProxyData):
    if proxy.auth:
        s = '{}://{}@{}:{}'.format(proxy.type, proxy.auth, proxy.ip, proxy.port)
    else:
        s = '{}://{}:{}'.format(proxy.type, proxy.ip, proxy.port)
    return s


class ParserException(Exception):
    def __init__(self, msg, *args: object) -> None:
        super().__init__(*args)
        self._msg = msg
    def __str__(self):
        return "ParserException({})".format(self._msg)


class BaseQueue:
    '''Базовый виртуальный класс для очереди на парсинг'''

    def reset(self):
        '''Очищает состояние очереди'''
        pass

    def put(self, links:[Link, List[Link]])->None:
        '''
        Добавляет в очередь для парсинга

        :param links: список ссылок
        :return:
        '''
        pass

    def has(self, typ: str = None) -> bool:
        '''проверяет наличие в очереди требуемых объектов'''
        pass

    def pop(self, cnt: int = 1, typ: str = None) -> list:
        '''выбирает из очереди требуемое количество объектов'''
        pass

    def save(self):
        pass

    def restore(self):
        pass

    def contains(self, link: Link) -> bool:
        '''проверяет наличие в очереди'''
        pass

    def __contains__(self, link) -> bool:
        '''проверяет наличи в очереди'''
        return self.contains(link)


class BaseHistory:
    '''Базовый виртуальный класс для истории парсинга'''

    def __init__(self):
        super(BaseHistory).__init__()

    def reset(self):
        '''сбрасывает историю парсинга'''
        pass

    def put(self, links:[Link, List[Link]]) -> None:
        '''добавляет в  историю'''
        pass

    def contains(self, link: Link) -> bool:
        '''проверяет наличи в истории'''
        pass

    def __contains__(self, link: Link) -> bool:
        '''проверяет наличи в истории'''
        return self.contains(link)

    def save(self):
        pass

    def restore(self):
        pass


class BaseParser():
    '''
    Реальный парсер должен поддерживать протокол мененджера контекста
    '''

    PARSED_TIME = 'parsed_at'  # время получения ответа
    PARSED_URL = 'parsed_url'  # URL где был получен ответ
    PARSED_STATUS = 'parsed_status'  # Ответ сервера
    PARSED_PROXY = 'parsed_proxy'  # Ответ сервера
    FIELD_URL = 'url'
    FIELD_NAME = 'name'
    FIELD_ARTICUL = 'articul'
    FIELD_PRICE = 'price' # число decimal
    FIELD_STOCK = 'stock' # число целое
    FIELD_DESCRIPTION = 'description'
    FIELD_IS_DESCRIPTION = 'is_description'
    FIELD_IS_INSTRUCTION = 'is_instruction'
    FIELD_IMAGES = 'images'
    FIELD_BIG_IMAGE = 'big_image'
    FIELD_SMALL_IMAGE = 'small_image'
    FIELD_CATEGORY = 'category'
    FIELD_BREADCRUMBS = 'breadcrumbs'
    FIELD_CHARACTERS = 'characters'  # характеристики товара без предварительно определенной структуры
    FIELD_PAGES = 'pages'  # список страниц категории (set)
    FIELD_SUBCATEGORIES = 'subcategories'  # список подкатегорий для рекуривного обхода
    FIELD_PRODUCTS = 'products' # товары (dict)

    def __init__(self, base_url, virtual_display=False, proxy:ProxyData=None):
        super().__init__()
        self._base_url = base_url
        self._virtual_display = virtual_display
        self._history = BaseHistory()
        self._queue = BaseQueue()
        self._proxy = proxy

    def base_url(self) -> str:
        '''возвращает корень сайта'''
        pass

    def url(self, link: Link) -> str:
        '''
        Возвращает URL для товара

        * id -- идентификатор товара на сайте. в частном случае это может быть URL

        * виртуальный метод.
        '''
        pass

    def parse_products(self, links:[Link, List[Link]], fields: set) -> [dict, None]:
        '''
        Парсит список товаров

        Обязательные параметры

        * links -- список товаров для парсинга
        * fields -- список собираемых полей

        Возвращает dict вида

        {
            id:{ field:value, field:value, field:value ...}, ...
        }

        результат должен содержать все ключи, переданные в параметре fields

        * виртуальный метод.
        '''
        pass

    def parse_product(self, link:Link, fields: set) -> [dict, None]:
        '''
        Парсит товар

        Обязательные параметры

        * link -- товар для парсинга
        * fields -- список собираемых полей

        Возвращает dict вида

        {
            field:value, field:value, field:value ...}, ...
        }

        результат должен содержать все ключи, переданные в параметре fields

        * виртуальный метод.
        '''
        pass

    def parse_categories(self, links:[Link, List[Link]], fields: set, product_fields: set = None) -> [dict, None]:
        '''
        Парсит список категорий, собирая список товаров

        Обязательные параметры

        * list_ids -- список категорий для парсинга
        * fields -- список собираемых полей для категорий
        * product_fields -- список собираемых полей для товаров

        Возвращает dict вида

        {
            id: {
                field:value, field:value, ...
            }
        }

        * метод не должен поднимать исключений
        * виртуальный метод
        '''
        pass

    def build_initial_list(self) -> bool:
        '''
        Cобирает начальный список категорий и/или товаров.

        Возвращает dict вида

        {
            categories:[id, id, ...],
            products:[id, id, ...],
        }

        * виртуальный метод
        '''
        pass

    def http_last_status(self):
        '''
        Возвращает статус последней страницы

        * виртуальный метод
        '''
        pass

    def proxy_string(self):
        if self._proxy:
            return format_proxy(self._proxy)
        return None

    def walk_site(self, reset=False):
        '''
        Выполняет полный обход сайта.
        В парсер в идеале умеет сохранять свое состояние, - то есть он может быть прерван,
        а затем его выполнение будет продолжено. для
        '''

        # это примерная схема работы парсера

        # categories_fields = {self.FIELD_TIME, self.FIELD_URL, self.FIELD_NAME}
        # products_fields = {self.FIELD_TIME, self.FIELD_URL, self.FIELD_NAME, self.FIELD_ARTICUL, self.FIELD_PRICE}
        #
        # if reset:
        #     site = self.build_initial_list()
        #     self.queue(category_ids=site.categories, product_ids=site.products)
        #
        # while self.queue_has_categories():
        #     parsed = self.parse_categories(self.queue_pop_categories(), categories_fields, products_fields)
        #     self.save_data()
        #     self.queue(parsed[self.FIELD_SUBCATEGORIES])
        #
        # while self.queue_has_products():
        #     parsed = self.parse_categories(self.queue_pop_categories(), categories_fields, products_fields)
        pass

    def save(self):
        self._history.save()
        self._queue.save()

    def restore(self):
        self._history.restore()
        self._queue.restore()

    def start_session(self):
        pass

    def sleep(self, x):
        sleep(x)

    def http_get(self, url, referrer, encoding=None)->[BeautifulSoup, None]:
        pass

    def get_ip(self):
        url = 'https://solotony.com/tools/proxy-checker/'
        soup = self.http_get(url, url)
        if not soup:
            logging.error('failed to get url=[{}]'.format(url))
            return None
        tag = soup.find('h1', attrs={'id': 'ip'})
        if not tag:
            logging.error('failed to detect h1.id=ip at url=[{}]'.format(url))
            return None

        text = tag.get_text(strip=True)
        if not re_ip.match(text):
            logging.error('bad IP value {} at url=[{}]'.format(text, url))
            return None

        logging.info('IP detected={} ({})'.format(text, self.__class__))
        return text