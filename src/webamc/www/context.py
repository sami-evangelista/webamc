#!/usr/bin/env python3

import fastapi as fapi
from sqlalchemy.orm.session import Session as ORMSession

from webamc.all import *
from webamc.db import op


class SessionNotOpenedException(Exception):
    pass


class Context:
    req: fapi.Request
    _dbs: None | ORMSession
    def __init__(self, req: fapi.Request) -> None:
        self.req = req
        self._dbs = None
    def __enter__(self) -> "Context":
        self._dbs = op.Session()
        self._dbs.begin()
        return self
    def __exit__(
            self,
            exc_type: None | tp.Type[Exception],
            exc_val: tp.Any,
            exc_tb: tp.Any
    ) -> None:
        if self._dbs is None:
            raise SessionNotOpenedException
        if exc_type is None:
            self._dbs.commit()
        else:
            self._dbs.rollback()
        self._dbs.close()
        self._dbs = None
    @property
    def dbs(self) -> ORMSession:
        if self._dbs is None:
            raise SessionNotOpenedException
        return self._dbs
