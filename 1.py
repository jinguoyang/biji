# -*- coding:utf-8 -*-
import random
from collections import Counter

from utils.singleton import Singleton
# count = 1

class AA(object):
    __metaclass__ = Singleton

    def __init__(self):
        self.cao = 0
        # count+=1

    def gan(self):
        self.cao += 1


def count():
    a = [i for i in range(13)]*3
    random.shuffle(a)
    b = a[:8]
    lis = Counter(b)
    for r, num in lis.most_common():
        if num > 3:
            return 1
    return 0


if __name__ == '__main__':
#     counts = 0
#     for i in range(200000):
#         counts+=count()
#
#     print counts
#     print counts/200000.0
    a = AA()
    a.gan()
    print a.cao
    b = AA()
    print b.cao
    b.gan()
    print b.cao
    print a.cao
    # def log(func):
    #     def wrapper():
    #         print 'call %s():' % func.__name__
    #         return func()
    #     return wrapper
    #
    #
    # @log
    # def now():
    #     print '2013-12-25'
    # now()
