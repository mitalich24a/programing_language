import sqlite3
import redis                 # pip install redis
import requests              # pip install requests

class Connections:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            obj = super().__new__(cls)
            obj.db    = sqlite3.connect("app.db")                  # DB connection
            obj.cache = redis.Redis(host="localhost", port=6379)   # Redis connection
            obj.api   = requests.Session()                         # third-party (HTTP) client
            obj.api.headers.update({"Authorization": "Bearer MY_KEY"})
            cls._instance = obj
        return cls._instance


# Usage
c1 = Connections()
c2 = Connections()

print(c1 is c2)                 # True
print(c1.db is c2.db)           # True
print(c1.cache is c2.cache)     # True
print(c1.api is c2.api)         # True


____________________________________________________________________________________

import sqlite3
import redis
import requests

class Connections:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            obj = super().__new__(cls)
            obj._db = None          # nothing connected yet
            obj._cache = None
            obj._api = None
            cls._instance = obj
        return cls._instance

    @property
    def db(self):
        if self._db is None:
            print("Connecting to DB...")
            self._db = sqlite3.connect("app.db")
        return self._db

    @property
    def cache(self):
        if self._cache is None:
            print("Connecting to Redis...")
            self._cache = redis.Redis(host="localhost", port=6379)
        return self._cache

    @property
    def api(self):
        if self._api is None:
            print("Creating API client...")
            self._api = requests.Session()
        return self._api


# Usage
conn = Connections()        # nothing connected yet

conn.db                     # Connecting to DB...
conn.db                     # (nothing printed, reused)
conn.cache                  # Connecting to Redis...
conn.cache                  # (reused)
