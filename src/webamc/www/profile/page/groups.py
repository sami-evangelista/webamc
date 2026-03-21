#!/usr/bin/env python3

from webamc.www.all import *
from webamc.db import queries, tables


def page(ctx: context.Context) -> he.Element:
    def get_rights(rights: list[types.usr_right_t]) -> he.Element:
        if not session.has_submission_right(ctx):
            return he.Empty()
        elements: list[he.Element] = list()
        rmap: dict[types.usr_right_t, types.txt_t] = {
            types.USR_RIGHT_VIEW: "name_view",
            types.USR_RIGHT_SUBMIT: "name_submission"
        }
        for i, r in enumerate(rights):
            if i > 0:
                elements.append(he.Str(" + "))
            elements.append(he.Txt(rmap[r]))
        return he.ElementList(*elements)

    groups: dict[int, tuple[tables.Grp, list[types.usr_right_t]]] = dict()
    for grp, usr_grp in queries.get_grps(ctx.dbs, session.usr_id(ctx)):
        groups.setdefault(grp.grp_id, (grp, list()))[1].append(
            usr_grp.ugp_right
        )
    tr_groups = list()
    if session.has_submission_right(ctx):
        tr_groups.append(he.Tr(he.Td(), he.Td(he.Txt("name_rights"))))
    tr_groups += [
        he.Tr(
            he.Td(he.Div(he.Str(grp.grp_name), class_="group-name")),
            he.Td(get_rights(rights))
        )
        for grp, rights in groups.values()
    ]
    result = he.Table(*tr_groups)
    return result
