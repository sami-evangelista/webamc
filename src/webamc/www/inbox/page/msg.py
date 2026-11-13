from webamc.www.all import *
from webamc.db import tables


def page(ctx: context.Context, msg_id: int) -> fa.Response:
    msg = ctx.dbs.query(tables.Message).get(msg_id)
    if msg is None:
        raise fa.HTTPException(status_code=404)
    if msg.msg_to != session.usr_id(ctx):
        raise fa.HTTPException(status_code=403)
    if msg.msg_type != types.MESSAGE_TYPE_FILE:
        raise fa.HTTPException(status_code=422)
    assert msg.msg_file_content is not None
    assert msg.msg_file_name is not None
    headers = {
        "Content-Disposition": f"attachment; filename=\"{msg.msg_file_name}\""
    }
    return fa.Response(
        headers=headers,
        content=msg.msg_file_content,
        media_type=mtype.get_mtype(Path(msg.msg_file_name))
    )
