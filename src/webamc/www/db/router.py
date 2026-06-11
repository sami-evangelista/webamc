from webamc.www.all import *
from webamc.db import util as db_util
from . import util


router = fa.APIRouter()


def _check_right(ctx: context.Context, query: types.db_query_t) -> None:
    if not util.has_right_to_execute(ctx, query):
        raise fa.HTTPException(status_code=403)


@router.post("/db/oper/query")
def route_query(
        req: fa.Request,
        query: types.db_query_t | list[types.db_query_t]
) -> fa.Response:
    from .oper import query as oper_query
    with context.Context(req) as ctx:
        return oper_query.data(ctx, query)


@router.get("/db/page/input")
def route_input(
        req: fa.Request,
        id_: str,
        col: str,
        col_id: str
) -> fa.Response:
    from .page import input as input_
    with context.Context(req) as ctx:
        session.check_logged_in(ctx)
        tbl = db_util.get_tbl_name(db_util.get_col_tbl(col))
        query: types.db_query_t = {
            "type": "select",
            "table": tbl,
            "where": [{"col": col_id, "op": "=", "val" : int(id_)}],
            "values": dict()
        }
        _check_right(ctx, query)
        return input_.page(ctx, id_, col, col_id)
