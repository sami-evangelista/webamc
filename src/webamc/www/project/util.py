from webamc.www.all import *
from webamc.db import tables


def get_project(ctx: context.Context, prj_id: int) -> tables.Project:
    result = ctx.dbs.query(
        tables.Project
    ).where(
        tables.Project.prj_id == prj_id
    ).first()
    if result is None:
        raise fa.HTTPException(status_code=404)
    if result.prj_usr != session.usr_id(ctx):
        raise fa.HTTPException(status_code=403)
    return result
