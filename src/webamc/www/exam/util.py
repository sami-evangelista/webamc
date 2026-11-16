from webamc.www.all import *
from webamc.db import queries, tables
from webamc.util import fmt


def get_exam(
        ctx: context.Context,
        exm_id: int
) -> tuple[tables.Item, tables.Exam]:
    result = next(
        (item_exam
         for item_exam in queries.get_usr_exams(
                 ctx.dbs, session.usr_id(ctx)
         )
         if item_exam[1].exm_id == exm_id), None
    )
    if result is None:
        raise fa.HTTPException(status_code=403)
    return result


def get_exams_select(
        ctx: context.Context,
        null_allowed: bool=True
) -> tuple[list[tuple[tables.Item, tables.Exam]], he.Element]:
    def format_exam(exam: tables.Exam) -> str:
        title = exam.exm_title
        return title + " (" + fmt.fmt_datetime(exam.exm_start) + ")"
    opts = list()
    exams = queries.get_usr_exams(ctx.dbs, session.usr_id(ctx))
    if null_allowed:
        opts.append(he.Option(he.Str("-"), value=""))
    opts += [
        he.Option(he.Str(format_exam(exam)), value=exam.exm_id)
        for _, exam in exams
    ]
    select = he.Select(
        *opts,
        id_="exm_id"
    ).set_data(
        "type", "integer"
    )
    return exams, select


def get_usrs_select(
        ctx: context.Context,
        grps_ids: set[int],
        id_: str = "usr_id",
        null_allowed: bool = True
) -> he.Select:
    query_usrs = queries.get_grps_usrs(ctx.dbs, grps_ids, types.USR_RIGHT_VIEW)
    opts = [
        he.Option(he.Str(usr.fmt()), value=usr.usr_id)
        for usr in query_usrs
    ]
    result: he.Select = he.Select(
        *opts,
        id_=id_
    )
    result.set_data(
        "type", "integer"
    )
    result.sort()
    if null_allowed:
        result.insert(0, he.Option(he.Str("-"), value=""))
    return result
