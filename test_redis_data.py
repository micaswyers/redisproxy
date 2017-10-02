import redis

r = redis.StrictRedis(host='redis', port=6379)

r.set("name", "Robert Kevin")
r.set("age", 111)
r.set("favfood", "pizza")
r.set("height", 100)
