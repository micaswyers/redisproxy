from datetime import datetime
from collections import OrderedDict
import socket

class LastUpdatedDict(OrderedDict):
    """Dict that keeps track of the order in which items were added/updated"""

    def __setitem__(self, key, value):
        if key in self:
            del self[key]
        OrderedDict.__setitem__(self, key, value)


class LRUCache(object):
    """Least Recently Used Cache supporting eviction based on capacity & TTL"""

    def __init__(self, capacity=100, ttl=7200):
        self.capacity = capacity
        self.ttl = ttl
        self.cache = LastUpdatedDict()


    def get(self, key):
        """Checks if key is in cache
            :param key (str)
            :returns: val (str) if exists or None
        """

        if self.cache.get(key) is not None:
            val, time_added = self.cache.pop(key)
            if (datetime.now() - time_added).total_seconds() >= self.ttl:
                return None
            self.cache[key] = (val, datetime.now())
            return val
        else:
            return None


    def set(self, key, val):
        """Sets key-val pair in self.cache
            :param key (str):
            :param val (str):
        """

        if len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = (val, datetime.now())


class RedisProxy(object):
    """Lightweight Read Cache for Redis GET commands"""

    def __init__(self, capacity, ttl, timeout=30):
        """Settings are configurable for Redis Proxy:
            :param capacity (int): number of keys to hold in cache
            :param ttl (int): # of seconds that a key can live in cache
        """

        self.redis_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.redis_socket.settimeout(timeout)
        self.redis_socket.connect(('', 6379))

        self.cache = LRUCache(capacity, ttl)

    def get(self, key):
        """Takes in a key, checks cache then backing Redis for value.
            Stores unstored keys in cache.
            :param key (str):
            :returns: value stored in Redis, if not already in cache
        """

        # First, check the cache
        cached_val = self.cache.get(key)
        if cached_val:
            return cached_val
        get_str = "*2\r\n$3\r\nGET\r\n$%s\r\n%s\r\n" % (len(key), key)
        self.redis_socket.sendall(get_str.encode('utf-8'))

        resp = self.redis_socket.recv(4096).decode('utf-8')
        # If Redis responds w/ a nil bulk string, return None to client
        if resp == "$-1\r\n":
            return None
        msg_type, body = resp[0], resp[1:].split("\r\n")
        length = body[0]
        redis_val = body[1]

        # Save it in the cache, if it's not already there
        self.cache.set(key, redis_val)

        return redis_val

r = RedisProxy(capacity=3, ttl=15)
