import sqlalchemy as sa
from sqlalchemy.orm import mapped_column, DeclarativeBase


def wrap_column(*args, **kwargs):
    return mapped_column(*args, nullable=False, **kwargs)


class Base(DeclarativeBase):
    pass


class SocUser(Base):
    __tablename__ = 'soc_user'
    login = mapped_column(sa.String(64), primary_key=True)
    pswd = wrap_column(sa.String(64))
    name = wrap_column(sa.String(64))
    email = wrap_column(sa.String(64))


class Post(Base):
    __tablename__ = 'post'
    id_ = mapped_column(sa.Integer, primary_key=True)
    author_id = wrap_column(sa.ForeignKey(SocUser.login))
    content = wrap_column(sa.String(255))

class Reaction(Base):
    __tablename__ = 'reaction'
    is_like = wrap_column(sa.Boolean)
    post = wrap_column(sa.ForeignKey(Post.id_, ondelete="CASCADE"), primary_key=True)
    likee = wrap_column(sa.ForeignKey(SocUser.login, ondelete="CASCADE"), primary_key=True)

    #pk = sa.PrimaryKeyConstraint(id_, post, likee, name="reaction_pk"),
    
