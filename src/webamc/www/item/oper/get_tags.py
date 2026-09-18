from typing import Any
from sqlalchemy import select

from webamc.db import tables
from webamc.www.all import *


def get_all_tags(ctx: context.Context) -> list[dict[str, Any]]:
    stmt = select(tables.Tag)
    res = ctx.dbs.execute(stmt)
    return [
        {
            "tag_id": tag.tag_id,
            "tag_name": tag.tag_name,
            "tag_desc": tag.tag_desc,
            "tag_color": tag.tag_color
        }
        for tag in res.scalars().all()
    ]
