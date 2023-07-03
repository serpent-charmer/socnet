import os
from typing import Annotated, Any, AsyncGenerator
from fastapi import Depends

from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

DB_URL = os.getenv("DB_URL", "127.0.0.1")
DATABASE_URL = f"postgresql+asyncpg://socnet:password@{DB_URL}/prod"

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, Any]:
    async with async_session() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise
        finally:
            await session.close()

SessionDependency = Annotated[AsyncSession, Depends(get_session)]
