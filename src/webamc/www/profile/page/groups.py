from webamc.www.all import *
from webamc.db import queries, tables


def page(ctx: context.Context) -> he.Element:
    def get_rights(rights: list[types.usr_right_t]) -> he.Element:
        if not session.has_submission_right(ctx):
            return he.Empty()
        elements: list[he.Element] = list()
        rmap: dict[types.usr_right_t, types.txt_t] = {
            types.USR_RIGHT_VIEW: "word_view",
            types.USR_RIGHT_SUBMIT: "word_submission"
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
    trs = list()
    if session.has_submission_right(ctx):
        trs.append([he.Empty(), he.Txt("word_rights")])
    trs += [
        [he.Div(he.Str(grp.grp_name), class_="group-name"), get_rights(rights)]
        for grp, rights in groups.values()
    ]
    result = he.mktable(trs)
    return result
