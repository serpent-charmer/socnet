

from typing import List
from pydantic import BaseModel
from redis.asyncio import Redis
from app import post
from app.rds import REDIS_URL
from purse.collections import RedisHash


class PostReactionCache(BaseModel):
    is_like: bool
    likee: str


r = Redis(host=REDIS_URL)


async def add_reaction(k: str, prc: PostReactionCache):
    reactions = RedisHash(r, f"post_reactions:{k}", PostReactionCache)
    await reactions.set(prc.likee, prc)


async def rem_reaction(k: str, likee: str):
    reactions = RedisHash(r, f"post_reactions:{k}", PostReactionCache)
    await reactions.delete(likee)


async def get_all(k: str):
    reactions = RedisHash(r, f"post_reactions:{k}", PostReactionCache)
    return [r async for r in reactions.values()]
