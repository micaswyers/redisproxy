import time
import mock
import unittest

from redisproxy import (
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

    def test_lru_set_capacity(self):
        """Test that inserting data obeys capacity limit"""

        testcache = LRUCache(capacity=3, ttl=15)
        testcache.set('radish', 'moo')
        testcache.set('rice', 'bap')
        testcache.set('beef', 'sogogi')
        self.assertEqual(len(testcache.cache), 3)

        testcache.set('egg', 'gyeran')
        self.assertEqual(len(testcache.cache), 3)
        self.assertEqual(
            testcache.cache.keys(),
            ['rice', 'beef', 'egg'],
        )


    @mock.patch('redisproxy.datetime')
    def test_timestamp_added_with_set(self, dt_mock):
        """Test that correct datetime is added for inserted data"""

        dt_mock.now.return_value = "2017-09-25 00:00:00"

        testcache = LRUCache()
        testcache.set('radish', 'moo')
        val, timestamp = testcache.cache['radish']
        self.assertEqual(timestamp, "2017-09-25 00:00:00")

    def test_get_not_in_cache_returns_None(self):
        """Test that getting a nonexistent value returns None"""

        testcache = LRUCache()
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

        testcache = LRUCache(ttl=86400)
        testcache.set('radish', 'moo')
        self.assertEqual(testcache.get('radish'), 'moo')


class RedisProxyTests(unittest.TestCase):

    def test_cached_val_returned(self):
        """Test that a value in the proxy's cache is returned, w/o calling Redis"""
        pass

    def test_nil_string_returned_from_Redis(self):
        """Test that a nil string from Redis cause proxy to return None"""
        pass

    def test_cache_new_data(self):
        """Test that data fetched from Redis is put into the proxy's cache"""
        pass


if __name__ == "__main__":
    unittest.main()
