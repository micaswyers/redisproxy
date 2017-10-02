# RedisProxy

This is a transparent Redis-proxy ("the proxy") serving with cached GET commands. It implements a subset of the Redis protocol. Of note:

  - GET commands are cached by the proxy
  - The cache is configured with LRU (Least Recently Used) eviction of keys and a max. size determined by number of keys
  - There is a single backing instance of Redis

# High-level Architecture Overview
At a high level, the proxy exists as an intermediate layer between the client and the single backing Redis server.


# What the Code Does
  - Parse config arguments from command line
  - Instantiates RedisProxy, which connects to backing Redis instance, instantiates a cache, and opens a listening socket
  - When a client connects, a new client socket is created.
  - When a client sends the proxy a Redis command, the proxy sends it to the Redis server.
  * Notably: any GET commands are cached by the proxy. (If those key-value pairs have already been retrieved, they will be stored in the cache [OrderedDict, under the hood].)
  * The cache is configured to evict the least-recently used key-value pairs when it is full. (Size is determined in number of keys.)
  * The cache also has a Time to Live (TTL) setting. Any keys that are past the TTL are evicted upon next access, and Redis is called, as if they keys were never there.
- The response is parsed (and saved to the cache with a timestamp if this is a GET command) and then send to the user

# Running the proxy
To run the proxy (I'm going to assume locally, for now.):
Run the Redis-server
    ```sh
    redis-server
    ```
Run the proxy:
    ```sh
    python redisproxy.py
    ```
(You can also run the proxy with configs:)
    ```sh
    python redisproxy.py --addr='localhost' --ttl=7200 --capacity=1000
    ```
Start up a client, such as using nc or telnet, in another window
    ```sh
    nc localhost 9999
    ```

Once the client connects, you can pass Redis commands to the proxy:
```sh
nc localhost 9999
PING
PONG
GET name
mica
GET age
100
HGETALL myhash
4
$3
foo
$3
bar
$3
baz
$5
blarf
```

# Timing Breakdown
  - Writing the proxy: ~9 hours, incl. writing code, manual testing, research about libraries
  - Refactoring code after initial review: 2 hours
  - Implementing Threaded proxy: 5-6 hours, incl. learning SocketServer
  - Writing tests/Setting up Docker: 8 hours, incl. thrashing about end-to-end tests
  - ReadMe: 30 minutes
