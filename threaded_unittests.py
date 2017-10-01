import time
import mock
import unittest

from threaded_proxy import (
    LastUpdatedDict,
    LRUCache,
    RedisProxy,
)


class TestLastUpdatedDict(unittest.TestCase):

    def test_order_preserved_with_insertions(self):
        """Test that items are stored in order they are inserted/updated"""

        test_dict = LastUpdatedDict()

        test_dict['apple'] = 'red'
        test_dict['orange'] = 'orange'
        test_dict['durian'] = 'brown'

        self.assertEqual(
            test_dict.keys(),
            ['apple', 'orange', 'durian'],
        )

        test_dict['apple'] = 'green'

        self.assertEqual(
            test_dict.keys(),
            ['orange', 'durian', 'apple'],
        )


class TestLRUCache(unittest.TestCase):

    def test_lru_cache_no_args(self):
        """Test instantiating LRUCache w/o capacity & ttl raises TypeError"""

        with self.assertRaises(TypeError):
            LRUCache(ttl=7200)

        with self.assertRaises(TypeError):
            LRUCache(capacity=100)


    def test_lru_set_capacity(self):
        """Test that inserting data obeys capacity limit"""

        testcache = LRUCache(capacity=3, ttl=15)
        testcache.set('radish', 'moo')
        testcache.set('rice', 'bap')
        testcache.set('beef', 'sogogi')
        self.assertEqual(len(testcache.data), 3)

        testcache.set('egg', 'gyeran')
        self.assertEqual(len(testcache.data), 3)
        self.assertEqual(
            testcache.data.keys(),
            ['rice', 'beef', 'egg'],
        )


    @mock.patch('threaded_proxy.datetime')
    def test_timestamp_added_with_set(self, dt_mock):
        """Test that correct datetime is added for inserted data"""

        dt_mock.now.return_value = "2017-09-25 00:00:00"

        testcache = LRUCache(capacity=100, ttl=7200)
        testcache.set('radish', 'moo')
        val, timestamp = testcache.data['radish']
        self.assertEqual(timestamp, "2017-09-25 00:00:00")

    def test_get_not_in_cache_returns_None(self):
        """Test that getting a nonexistent value returns None"""

        testcache = LRUCache(capacity=100, ttl=7200)
        testcache.set('radish', 'moo')
        self.assertIsNone(testcache.get('ddeok'))


    def test_get_in_cache_expired_returns_None(self):
        """Test that expired value returns None"""

        testcache = LRUCache(capacity=3, ttl=2)
        testcache.set('radish', 'moo')
        time.sleep(2)
        self.assertIsNone(testcache.get('radish'))

    def test_get_in_cache_unexpired(self):
        """Test that an unexpired cached value is returned"""

        testcache = LRUCache(capacity=100, ttl=86400)
        testcache.set('radish', 'moo')
        self.assertEqual(testcache.get('radish'), 'moo')


class RedisProxyTests(unittest.TestCase):

    @mock.patch('threaded_proxy.RedisProxy._open_redis_connection')
    def setUp(self, patched_redis):
        """Sets up a test proxy with mocked Redis and client connections"""

        self.testproxy = RedisProxy(capacity=5, ttl=7200)
        self.testproxy.cache.set('foo', 'bar')

    def test_cached_val_returned(self):
        """Test that a value in the proxy's cache is returned, w/o calling Redis"""

        self.testproxy.redis_socket.recv.return_value = "$3\r\nbar\r\n"

        cached_val = self.testproxy.get('foo')

        self.assertEqual(cached_val, 'bar')
        self.testproxy.redis_socket.sendall.assert_not_called()
        self.testproxy.redis_socket.recv.assert_not_called()


    def test_nil_string_returned_from_Redis(self):
        """Test that a nil string from Redis cause proxy to return None"""

        # Mocking out a nil return from backing Redis
        self.testproxy.redis_socket.recv.return_value = "$-1\r\n"

        self.assertIsNone(self.testproxy.get('blarf'))
        self.testproxy.redis_socket.sendall.assert_called()
        self.testproxy.redis_socket.recv.assert_called()


    def test_cache_new_data(self):
        """Test that data fetched from Redis is put into the proxy's cache"""

        self.testproxy.redis_socket.recv.return_value = "$5\r\nblarf\r\n"

        ret_val = self.testproxy.get('baz')
        self.assertEqual(ret_val, self.testproxy.cache.get('baz'))


if __name__ == "__main__":
    unittest.main()
