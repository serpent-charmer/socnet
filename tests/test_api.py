from copy import deepcopy
from datetime import datetime, timedelta
import json
import os
import selectors
from fastapi import Depends, FastAPI
from httpx import AsyncClient
import pytest
import asyncio
import pytest_asyncio
from typing import Annotated, Any, AsyncGenerator, List
from sqlalchemy import NullPool, func, update

from sqlalchemy.schema import CreateSchema
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

from fastapi.testclient import TestClient
from app import app
from app.rds import redis_instanse
from db.models import Base
from db.session import DATABASE_URL, get_session

test_schema = "test"
engine = create_async_engine(DATABASE_URL, echo=False, execution_options={
                             "schema_translate_map": {None: test_schema}},
                             poolclass=NullPool)
async_session = async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def client(myapp: FastAPI):
    async with AsyncClient(app=myapp, base_url="http://testserver") as client:
        yield client


@pytest.fixture(scope="session")
def event_loop():
    selector = selectors.SelectSelector()
    loop = asyncio.SelectorEventLoop(selector)
    yield loop
    loop.close()


# @pytest_asyncio.fixture
async def sess() -> AsyncGenerator[AsyncSession, Any]:
    async with async_session() as session:
        try:
            yield session
        except:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def init_schema():
    async with engine.begin() as conn:
        check = await conn.run_sync(engine.dialect.has_schema, test_schema)
        if not check:
            await conn.execute(CreateSchema(test_schema))


@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="function", autouse=True)
async def redis_init():
    await redis_instanse.flushall()


@pytest.fixture(scope="session", autouse=True)
def myapp():
    app.dependency_overrides[get_session] = sess
    return app


async def make_user(c, usr):
    rs = await c.post("/account/signup",
                      json=usr,
                      follow_redirects=True)
    h = rs.json()
    acc = h["access_token"]
    headers = {
        "Authorization": f"Bearer {acc}"
    }
    return headers


async def test_no_such_post(client: AsyncClient):

    ud = dict({"login": "test1",
               "pswd": "test",
               "name": "1234",
               "email": "test@org"})

    ud1 = dict({"login": "test2",
                "pswd": "test",
                "name": "1234",
                "email": "test@org"})

    headers = await make_user(client, ud)
    headers1 = await make_user(client, ud1)

    await client.post("/post/add",
                      headers=headers1,
                      json={"content": "hello"})

    rs = await client.post("/post/react",
                           headers=headers,
                           json={"post_id": 0,
                                 "is_like": True})

    m = json.loads(rs.content)["message"]
    assert rs.status_code == 400 and m == "No such post"

    rs = await client.post("/post/list",
                           headers=headers,
                           json={"post_id": 1})

    print(rs, rs.content)

    rs = await client.post("/post/getreact",
                           headers=headers,
                           json={"post_id": 1})

    print(rs, rs.content)


async def test_like_other(client: AsyncClient):

    ud = dict({"login": "test1",
               "pswd": "test",
               "name": "1234",
               "email": "test@org"})

    ud1 = dict({"login": "test2",
                "pswd": "test",
                "name": "1234",
                "email": "test@org"})

    headers = await make_user(client, ud)

    await client.post("/post/add",
                      headers=headers,
                      json={"content": "hello"})

    rs = await client.post("/post/react",
                           headers=headers,
                           json={"post_id": 1,
                                 "is_like": True})

    m = json.loads(rs.content)["message"]
    assert rs.status_code == 400 and "Like" in m


async def test_react(client: AsyncClient):

    ud = dict({"login": "test1",
               "pswd": "test",
               "name": "1234",
               "email": "test@org"})

    ud1 = dict({"login": "test2",
                "pswd": "test",
                "name": "1234",
                "email": "test@org"})

    headers = await make_user(client, ud)
    headers1 = await make_user(client, ud1)

    await client.post("/post/add",
                      headers=headers,
                      json={"content": "hello"})

    rs = await client.post("/post/react",
                           headers=headers1,
                           json={"post_id": 1,
                                 "is_like": True})

    print(rs, rs.content)

    rs = await client.post("/post/list",
                           headers=headers,
                           json={"post_id": 1})

    print(rs, rs.content)

    rs = await client.post("/post/getreact",
                           headers=headers,
                           json={"post_id": 1})
    r = rs.json()[0]

    print(r)

    rs = await client.post("/post/remreact",
                           headers=headers,
                           json={"post_id": 1})

    rs = await client.post("/post/getreact",
                           headers=headers,
                           json={"post_id": 1})
    r = rs.json()[0]

    print(r)

    assert r["likee"] == "test2"


async def test_rem_react(client: AsyncClient):

    ud = dict({"login": "test1",
               "pswd": "test",
               "name": "1234",
               "email": "test@org"})

    ud1 = dict({"login": "test2",
                "pswd": "test",
                "name": "1234",
                "email": "test@org"})

    headers = await make_user(client, ud)
    headers1 = await make_user(client, ud1)

    await client.post("/post/add",
                      headers=headers,
                      json={"content": "hello"})

    rs = await client.post("/post/react",
                           headers=headers1,
                           json={"post_id": 1,
                                 "is_like": True})

    print(rs, rs.content)

    rs = await client.post("/post/list",
                           headers=headers,
                           json={"post_id": 1})

    print(rs, rs.content)

    rs = await client.post("/post/getreact",
                           headers=headers,
                           json={"post_id": 1})
    r = rs.json()[0]

    print(r)

    rs = await client.post("/post/remreact",
                           headers=headers1,
                           json={"post_id": 1})

    print(rs)

    rs = await client.post("/post/getreact",
                           headers=headers,
                           json={"post_id": 1})
    r = rs.json()

    assert len(r) == 0


async def test_rem_post(client: AsyncClient):

    ud = dict({"login": "test1",
               "pswd": "test",
               "name": "1234",
               "email": "test@org"})

    ud1 = dict({"login": "test2",
                "pswd": "test",
                "name": "1234",
                "email": "test@org"})

    headers = await make_user(client, ud)
    headers1 = await make_user(client, ud1)

    await client.post("/post/add",
                      headers=headers,
                      json={"content": "hello"})

    rs = await client.post("/post/react",
                           headers=headers1,
                           json={"post_id": 1,
                                 "is_like": True})

    print(rs, rs.content)

    rs = await client.post("/post/list",
                           headers=headers,
                           json={"post_id": 1})

    print(rs, rs.content)

    rs = await client.post("/post/getreact",
                           headers=headers,
                           json={"post_id": 1})
    r = rs.json()[0]

    print(r)

    rs = await client.post("/post/rem",
                           headers=headers1,
                           json={"post_id": 1})

    print(rs)

    rs = await client.post("/post/getreact",
                           headers=headers,
                           json={"post_id": 1})
    r = rs.json()

    assert len(r) == 0
