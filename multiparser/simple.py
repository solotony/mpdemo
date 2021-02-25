'''
    ____            _           _____
   / ___|    ___   | |   ___   |_   _|   ___    _ __    _   _
   \___ \   / _ \  | |  / _ \    | |    / _ \  | '_ \  | | | |
    ___) | | (_) | | | | (_) |   | |   | (_) | | | | | | |_| |
   |____/   \___/  |_|  \___/    |_|    \___/  |_| |_|  \__, |
   2020 (c) SoloTony.com                                |___/
   v 0.0.1 multi parser
'''

from collections import deque
from .base import Link, BaseHistory, BaseQueue
from typing import List

class SimpleQueue(BaseQueue):
    '''
    Простая очередь для парсинга. Все элементы хранятся в очереди и в множестве.
    Для каждого типа элементов создается своя пара - очередь и множество
    '''

    def __init__(self):
        super(BaseQueue).__init__()
        self._q = dict()
        self._s = dict()

    def reset(self):
        '''Очищает состояние очереди'''
        self._q = dict()
        self._s = dict()

    def put(self, links:[Link, List[Link]])->None:
        '''
        Добавляет в очередь для парсинга

        :param links: список ссылок
        :return:
        '''


        if type(links) != list:
            links = [links]
        for link in links:
            if link.type not in self._s:
                self._q[link.type] = deque()
                self._s[link.type] = set()
            if link in self._s[link.type]:
                continue
            self._s[link.type].add(link)
            self._q[link.type].append(link)


    def has(self, typ: str = None) -> bool:
        '''проверяет наличие в очереди требуемых объектов'''
        if typ != None:
            if typ not in self._s:
                return False
            return len(self._s[typ]) > 0
        for t in self._s:
            if len(self._s[t]) > 0:
                return True
        return False

    def pop(self, cnt: int = 1, typ: str = None) -> list:
        '''выбирает из очереди требуемое количество объектов. Возвращается массив пар (тип, id).
        Если тип не указан выбираются те что есть, порядок не определен'''
        result = []
        for t in self._s:
            if typ and typ != t:
                continue
            while len(result) < cnt and len(self._q[t]) > 0:
                e = self._q[t].popleft()
                self._s[t].remove(e)
                result.append(e)
        return result

    def contains(self, link: Link) -> bool:
        '''проверяет наличи в списке'''
        if link.type not in self._s:
            return False
        return link in self._s[link.type]

    def __str__(self):
        return 'Queue: ' + str({t: len(self._q[t]) for t in self._q})


class SimpleHistory(BaseHistory):
    def __init__(self):
        super(SimpleHistory).__init__()
        self._s = set()

    def reset(self):
        '''сбрасывает историю парсинга'''
        self._s = set()

    def put(self, links:[Link, List[Link]]) -> None:
        '''добавляет в  историю'''
        if type(links) != list:
            links = [links]
        for link in links:
            self._s.add(link)

    def contains(self,link: Link) -> bool:
        '''проверяет наличи в истории'''
        return link in self._s

    def __str__(self):
        return str('History: {} items'.format(len(self._s)))

