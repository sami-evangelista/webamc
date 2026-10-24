from fastapi.encoders import jsonable_encoder

from webamc.www.all import *
from webamc.db import util as db_util
from webamc.www.db import util as www_db_util, router


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:
    def build_where(where: types.db_where_t) -> tp.Any:
        col = db_util.get_col(where["col"])
        if where["op"] == "like":
            return col.like(str(where["val"]))
        return col == where["val"]
    def get_db_object_values(obj: tp.Any) -> types.db_map_t:
        return {
            col.name: getattr(obj, col.name)
            for col in db_util.get_tbl_cols(tbl)
        }
    session.check_logged_in(ctx)
    query = args["query"]
    if isinstance(query, list):
        queries = query
        single_query = False
    else:
        queries = [query]
        single_query = True
    for q in queries:
        router._check_right(ctx, q)
    rvalues: list[list[types.db_map_t]] = list()
    rrvalues: list[list[types.db_map_t]] = list()  # readable values
    for q in queries:
        tbl = db_util.get_tbl(q["table"])
        tbl_meta = db_util.get_tbl_meta(q["table"])
        typ = q["type"]
        values = q.get("values", dict())
        conds = [build_where(where) for where in q.get("where", list())]
        wheres = sa.and_(*conds)
        if typ == "delete":
            for o in ctx.dbs.scalars(sa.select(tbl_meta).where(wheres)):
                ctx.dbs.delete(o)
            rvalues.append([])
            rrvalues.append([])
        elif typ == "select":
            rvalues.append([
                get_db_object_values(obj)
                for obj in ctx.dbs.query(tbl).where(wheres)
            ])
            rrvalues.append([])
        elif typ == "insert":
            new_obj = tbl_meta(**values)
            ctx.dbs.add(new_obj)
            rvalues.append([get_db_object_values(new_obj)])
            rrvalues.append([])
        elif typ == "update":
            for o in ctx.dbs.scalars(sa.select(tbl_meta).where(wheres)):
                for k, v in values.items():
                    setattr(o, k, v)
            rvalues.append([dict(values.items())])
            rrvalues.append([{
                col_name: www_db_util.val_fmt(
                    ctx, db_util.get_col(col_name), val
                )[1]
                for col_name, val in values.items()
            }])
        ctx.dbs.commit()
    result: types.json_response_t = {
        "success": True,
        "msgs": list(),
        "result": {
            "values": rvalues[0] if single_query else rvalues,
            "readable_values": rrvalues[0] if single_query else rrvalues
        }
    }
    return fa.responses.JSONResponse(jsonable_encoder(result))
