#!/usr/bin/env python3

from webamc.www.all import *
from webamc.db import queries
from webamc.util import fmt


def page(
        ctx: context.Context,
        grp_id: int | None
) -> he.Element:
    if grp_id is not None:
        if grp_id not in session.usr_submit_groups(ctx):
            raise fa.HTTPException(status_code=403)
        grps = queries.get_grp_sub_grps(
            ctx.dbs,
            grp_id
        )
    else:
        grps = queries.get_usr_grps(
            ctx.dbs, 
            session.usr_id(ctx),
            types.USR_RIGHT_SUBMIT
        )
    children: list[he.Element] = [
        he.Li(
            he.Div(
                he.Str(grp.grp_name),
                class_="group-name",
                onclick=f"item_load_grp({grp.grp_id})",
                style="cursor: pointer;"
            ),
            he.Div(
                id_=f"div-group-body-{grp.grp_id}"
            ),
            class_="group-tree"
        )
        for grp in grps
    ]
    if grp_id is not None:
        usr_sorted = sorted(
            queries.get_grps_usrs(ctx.dbs, {grp_id}, types.USR_RIGHT_VIEW),
            key=lambda usr: (usr.usr_name, usr.usr_fst_name, usr.usr_code)
        )
        children += [
            he.Div(
                he.Str(
                    fmt.fmt_name(usr.usr_fst_name, usr.usr_name)
                    + " / " + usr.usr_code
                ),
                class_="usr-name"
            )
            for usr in usr_sorted
        ]
    return he.Ul(*children)
