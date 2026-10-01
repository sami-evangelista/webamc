from pathlib import Path

from webamc.www.all import *
from webamc.db import tables


def page(ctx: context.Context, msg_id: int) -> fa.Response:
    msg = ctx.dbs.query(tables.Message).get(msg_id)
    if msg is None:
        raise fa.HTTPException(status_code=404)
    if msg.msg_to != session.usr_id(ctx):
        raise fa.HTTPException(status_code=403)
    headers = {
        "Content-Disposition": f"attachment; filename=\"{msg.msg_filename}\""
    }
    return fa.Response(
        headers=headers,
        content=msg.msg_file,
        media_type=mtype.get_mtype(Path(msg.msg_filename))
    )
