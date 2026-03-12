#!/usr/bin/env python3

from webamc.www.all import *
from webamc.db import tables
from webamc.util import security
from webamc.www.auth import router


def data(
        ctx: context.Context,
        args: router.args_oper_login_local_t
) -> fa.Response:
    if not config.CONFIG["auth_local_enabled"]:
        raise fa.HTTPException(status_code=403)
    password_hash = security.hash_password(args["loc_password"])
    query = ctx.dbs.query(
        tables.Usr
    ).where(
        (tables.LocalAuth.loc_enabled)
        & (tables.LocalAuth.loc_password == password_hash)
        & (tables.LocalAuth.loc_usr == tables.Usr.usr_id)
        & (tables.LocalAuth.loc_login == args["loc_login"])
    )
    usr = query.first()
    if usr is None:
        return base.wrap_code("err_wrong_credentials")
    session.init(ctx, usr)
    return base.wrap_code("succ_login")
