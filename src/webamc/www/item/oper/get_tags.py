from sqlalchemy import select
from webamc.db import tables

def get_all_tags(ctx): # On reçoit le contexte ici
    """Getting all tags from database"""
    stmt = select(tables.Tag)
    
    res = ctx.dbs.execute(stmt)
    
    tags = [
        {
            "tag_id": tag.tag_id, 
            "tag_name": tag.tag_name, 
            "tag_desc": tag.tag_desc, 
            "tag_color": tag.tag_color
        } 
        for tag in res.scalars().all()
    ]
    return tags