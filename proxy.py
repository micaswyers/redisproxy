from argparse import ArgumentParser
from datetime import datetime
from collections import OrderedDict
import select
import socket

MAX_LISTENS = 5


class LastUpdatedDict(OrderedDict):
    """Dict that keeps track of the order in which items were added/updated"""

    def __setitem__(self, key, value):
        if key in self:
            del self[key]
        OrderedDict.__setitem__(self, key, value)


class LRUCache(object):
    """Least Recently Used Cache supporting eviction based on capacity & TTL"""

    def __init__(self, capacity=None, ttl=None):

        if not capacity:
            raise TypeError("Capacity cannot be None for LRUCache")
        if not ttl:
            raise TypeError("TTL cannot be None for LRUCache")
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

    def __init__(self,
        host_addr=None,
        port=6379,
        capacity=100,
        ttl=7200,
        timeout=30,
    ):
        """Settings are configurable for Redis Proxy:
            :param host_addr (str): IP address of backing Redis instance
            :param port (int): Port for Redis socket
            :param capacity (int): number of keys to hold in cache
            :param ttl (int): # of seconds that a key can live in cache
            :param timeout (int), seconds after which to timeout network request
        """

        self.cache = LRUCache(capacity, ttl)

        self.socket_list = []
        self.max_listens = MAX_LISTENS

        if not host_addr:
            host_addr = ''

        # Open Redis connection
        self.redis_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.redis_socket.settimeout(timeout)
        self.redis_socket.connect((host_addr, port))
        print "Connected to Redis on %s:%s" % (host_addr, port)

        # Open Client socket
        self.client_socket = self._open_connection(host='', port=5555)
        self.socket_list.append(self.client_socket)


    def run(self):
        running = True
        while running:
            # Listen for input sources (Redis & any client)
            in_ready, out_ready, err_ready = select.select(
                self.socket_list,
                [],
                [],
                0,
            )
            for src in in_ready:
                # New client connection, creates new client socket
                if src == self.client_socket:
                    new_sock, addr = self.client_socket.accept()
                    new_sock.sendall(
                        "Connected to RedisProxy\nYou can send GET {key} commands to the proxy\n",
                    )
                    self.socket_list.append(new_sock)
                # Input from a client connection that we've already seen
                else:
                    data = src.recv(4096).strip()
                    if data:
                        data = data.split()
                        if len(data) != 2 or data[0] != "GET":
                            src.sendall("Please use Redis 'GET key' command format\n\r")
                            continue
                        ret_val = self.get(data[1])
                        if ret_val is None:
                            src.sendall("Nothing exists for key %s in Redis\n\r" % (data[1]))
                            continue
                        ret_val = ret_val + "\n\r"
                        src.sendall(ret_val.encode('utf-8'))
                    else:
                        if src in self.socket_list:
                            self.socket_list.remove(src)
                            print "Client connection closed"
                        else:
                            continue
        self.redis_socket.close()
        self.client_socket.close()

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

    def _open_connection(self, host=None, port=None, timeout=30):

        if not host:
            host = socket.gethostname()
        if not port:
            raise TypeError("No port for listening socket passed in")
        try:
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.settimeout(timeout)
            my_socket.bind((host, port))
            my_socket.listen(MAX_LISTENS)
            print "Listening on %s:%s" % (host, port)
        except socket.error, (value, msg):
            if my_socket:
                    my_socket.close()
            print "Could not open socket: ", msg
            sys.exit(1)
        return my_socket


if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument(
        '--addr',
        type=str,
        dest='addr',
        default='',
        action='store',
        required=False,
        help='Enter addr of backing Redis (Defaults to '')',
    )

    parser.add_argument(
        '--ttl',
        type=int,
        dest='ttl',
        default=7200,
        action='store',
        required=False,
        help='Enter TTL (in sec. for keys in cache)',
    )

    parser.add_argument(
        '--capacity',
        type=int,
        dest='capacity',
        default=1000,
        action='store',
        required=False,
        help='Enter max. # of cache keys before LRU eviction',
    )

    args = parser.parse_args()

    RedisProxy(host_addr=args.addr, ttl=args.ttl, capacity=args.capacity).run()
