from webamc.www.all import *
from webamc.db import queries, tables


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
