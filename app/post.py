from typing import Any, Optional
from asyncpg import IntegrityConstraintViolationError
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import CursorResult, and_, delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert
from app.cache import PostReactionCache, add_reaction, get_all, rem_reaction
from app.security.jwt import Authorize
from db.models import Post, Reaction, SocUser

from db.session import SessionDependency


class SearchPost(BaseModel):
    author_name: Optional[str]
    li: Optional[int]
    off: Optional[int]


class CreatePost(BaseModel):
    content: str


class RemovePost(BaseModel):
    post_id: int


class ReactBase(BaseModel):
    post_id: int


class React(ReactBase):
    post_id: int
    is_like: bool


router = APIRouter(prefix="/post",
                   tags=["post"])


@router.post("/list")
async def plist(s: SearchPost, sess: SessionDependency, auth: Authorize):
    await auth.jwt_required()
    q = select(Post)
    if s.author_name:
        q = q.join(SocUser).where(SocUser.name == s.author_name)
    if s.li:
        q = q.limit(s.li)
    if s.off:
        q = q.offset(s.off)
    rs = await sess.execute(q)
    return rs.scalars().all()


@router.post("/add")
async def add(c: CreatePost, sess: SessionDependency, auth: Authorize):
    await auth.jwt_required()
    subj = await auth.get_jwt_subject()
    if subj is not None:
        await sess.execute(
            insert(Post)
            .values(author_id=subj, content=c.content))
        await sess.commit()


@router.post("/rem")
async def rem(pr: RemovePost, sess: SessionDependency, auth: Authorize):
    await auth.jwt_required()
    subj = await auth.get_jwt_subject()
    await rem_reaction(pr.post_id, subj)
    await sess.execute(delete(Post).where(Post.id_ == pr.post_id))


@router.post("/getreact")
async def getreact(r: ReactBase, auth: Authorize):
    await auth.jwt_required()
    return await get_all(r.post_id)


@router.post("/react")
async def react(r: React, sess: SessionDependency, auth: Authorize):
    await auth.jwt_required()
    subj = await auth.get_jwt_subject()
    q = select(Post)\
        .where(and_(Post.id_ == r.post_id,
                    Post.author_id == subj))
    rs = await sess.execute(q)
    if rs.scalar_one_or_none():
        return JSONResponse(status_code=400,
                            content={"message": "Like other posts not your own"})

    try:
        q = insert(Reaction)\
            .values(likee=subj, post=r.post_id, is_like=r.is_like)\
            .on_conflict_do_update(index_elements=["post", "likee"],
                                   set_=dict(is_like=r.is_like))
        rs = await sess.execute(q)
        await sess.commit()
        await add_reaction(r.post_id, PostReactionCache(likee=subj,
                                                        is_like=r.is_like))
    except IntegrityError as e:
        return JSONResponse(status_code=400,
                            content={"message": "No such post"})


@router.post("/remreact")
async def react(r: ReactBase, sess: SessionDependency, auth: Authorize):
    await auth.jwt_required()
    subj = await auth.get_jwt_subject()
    await rem_reaction(r.post_id, subj)
    await sess.execute(
        delete(Reaction)
        .where(Reaction.post == r.post_id,
               Reaction.likee == subj))
    await sess.commit()
