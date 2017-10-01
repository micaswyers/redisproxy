import redis
import socket
import threading
import unittest

from threaded_proxy import (
    RedisProxy,
    ThreadedTCPRequestHandler,
    ThreadedTCPServer,
)


REDIS = redis.StrictRedis(host='localhost', port=6379)


class EndToEndTests(unittest.TestCase):

    def setUp(self):

        REDIS.set('testkey', 'testval')


    def tearDown(self):
        REDIS.delete('testkey')


    def test_client(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 7777))
        welcome_str = 'You are connected to the RedisProxy. Type QUIT to close connection\n'
        welcome_msg = sock.recv(1024)
        self.assertEqual(welcome_str, welcome_msg)

        sock.close()

if __name__ == "__main__":
    # Run Redis Proxy
    redis_proxy = RedisProxy(host_addr='', ttl=15, capacity=3)
    server = ThreadedTCPServer(('localhost', 7777), ThreadedTCPRequestHandler)
    server.proxy = redis_proxy
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    unittest.main()

    server.shutdown()
    server.server_close()
