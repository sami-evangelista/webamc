from webamc.www.all import *
from webamc.www.exam import router
from webamc.db import queries, tables


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:
    exm_id = args["exm_id"]
    grp_id = args["grp_id"]
    usr_id = args["usr_id"]
    _, exam = router._get_exam(ctx, exm_id)
    to_register: set[int] = set()
    if grp_id is not None:
        query = ctx.dbs.query(
            tables.Grp
        ).where(
            tables.Grp.grp_id == grp_id
        )
        grp = query.first()
        if grp is None:
            raise fa.HTTPException(status_code=422)
        if grp.grp_id not in session.usr_submit_groups(ctx):
            raise fa.HTTPException(status_code=403)
        grps = queries.get_grp_tree(ctx.dbs, grp_id)
        usr_ids = set(
            usr.usr_id
            for usr in queries.get_grps_usrs(
                    ctx.dbs, grps, types.USR_RIGHT_VIEW
            )
        )
        to_register = to_register.union(usr_ids)
    if usr_id is not None:
        if not queries.is_in_grps(
                ctx.dbs,
                usr_id,
                set(session.usr_submit_groups(ctx).keys()),
                types.USR_RIGHT_VIEW
        ):
            raise fa.HTTPException(status_code=403)
        to_register.add(usr_id)
    query_prev = ctx.dbs.query(
        tables.Registration
    ).where(
        (tables.Registration.reg_exam == exam.exm_id)
        & (tables.Registration.reg_usr.in_(to_register))
    )
    prev = {reg.reg_usr for reg in query_prev}
    for usr in to_register - prev:
        reg = tables.Registration(
            reg_usr=usr,
            reg_exam=exam.exm_id
        )
        ctx.dbs.add(reg)
    added = len(to_register) - len(prev)
    txt = lang.txt("param_seq_registrations_done", str(added))
    response = {
        "success": True,
        "msgs": [txt],
        "result": None
    }
    return fa.responses.JSONResponse(response)
