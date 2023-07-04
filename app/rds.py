import os

from redis.asyncio import Redis
from purse.collections import RedisHash


REDIS_URL = os.getenv("REDIS_URL", "127.0.0.1")
redis_instanse = Redis(host=REDIS_URL)
tokens = RedisHash(redis_instanse, "jwts", str)

async def check_token(token):
    rs = await tokens.contains(token)
    return not rs


async def revoke_token(token):
    await tokens.delete(token)


async def add_token(token):
    await tokens.set(token, "")
