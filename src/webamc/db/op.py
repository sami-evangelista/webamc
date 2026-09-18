from sqlalchemy.orm.session import Session as ORMSession
from sqlalchemy.orm.session import sessionmaker

from webamc.all import *


conn: sa.engine.base.Connection
engine: sa.engine.base.Engine
conn_done: bool = False
Session: sessionmaker[ORMSession]  # pylint: disable=unsubscriptable-object


def connect() -> None:
    global conn
    global engine
    global conn_done
    global Session
    url = sa.engine.url.URL.create(
        "postgresql",
        database=config.CONFIG["db_name"],
        username=config.CONFIG["db_user"],
        password=config.CONFIG["db_password"],
        host=config.CONFIG["db_host"],
        port=config.CONFIG["db_port"]
    )
    engine = sa.create_engine(url)
    conn = engine.connect()
    conn_done = True
    Session = sessionmaker(bind=engine)


def close() -> None:
    if conn_done:
        conn.close()


def init() -> None:
    from . import tables
    tables.Base.metadata.drop_all(engine)
    tables.Base.metadata.create_all(engine)
