#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.exam import router
from webamc.db import queries, tables


def data(
        ctx: context.Context,
        args: router.args_oper_register_group_t
) -> fa.Response:
    query = ctx.dbs.query(
        tables.Grp
    ).where(
        tables.Grp.grp_id==args["grp_id"]
    )
    grp = query.first()
    if grp is None:
        raise fa.HTTPException(status_code=422)
    if args["grp_id"] not in session.usr_submit_groups(ctx):
        raise fa.HTTPException(status_code=403)
    mcq, item, exam = router._get_exam(ctx, args["exm_id"])
    grps = queries.get_grp_tree(ctx.dbs, args["grp_id"])
    usrs = set(
        usr.usr_id
        for usr in queries.get_grps_usrs(
                ctx.dbs, grps, types.USR_RIGHT_VIEW
        )
    )
    usrs_prev = {
        reg.reg_usr
        for reg in ctx.dbs.query(
                tables.Registration
        ).where(
            (tables.Registration.reg_exam == exam.exm_id)
            & (tables.Registration.reg_usr.in_(usrs))
        ).all()
    }
    for usr in usrs - usrs_prev:
        reg = tables.Registration(
            reg_usr=usr,
            reg_exam=exam.exm_id
        )
        ctx.dbs.add(reg)
    return fa.responses.JSONResponse({
        "success": True,
        "msgs": [
            lang.txt("param_seq_registrations_done")
            % str(len(usrs - usrs_prev))
        ],
        "result": None
    })
