import datetime

from webamc.db import tables
from webamc.www.all import *
from . import save


def data(
        ctx: context.Context,
        mcq_result: types.args_route_mcq_result_t
) -> fa.Response:

    itm_id = mcq_result["itm_id"]
    session.check_can_view_mcq(ctx, itm_id)
    usr_id = session.usr_id(ctx)

    # create review submission linked to user and mcq
    sub = tables.Submission(
        sub_type=types.SUBMISSION_TYPE_REVIEW,
        sub_date=datetime.datetime.now(),
        sub_rev_usr=usr_id,
        sub_rev_mcq=itm_id
    )
    ctx.dbs.add(sub)
    ctx.dbs.flush()

    save._save_submission(ctx, sub.sub_id, mcq_result)
    ctx.dbs.commit()

    # compute live correction for choices and questions
    corr: dict[tp.Literal["cho", "qst"], dict[int, bool]] = {
        "cho": dict(),
        "qst": dict()
    }
    for cho_id, cho_checked in mcq_result["choices"].items():
        row = ctx.dbs.query(
            tables.Item,
            tables.ItemRelation
        ).where(
            (tables.Item.itm_id == int(cho_id))
            & (tables.Item.itm_id == tables.ItemRelation.itr_child)
        ).first()
        assert row is not None
        choice, relation = row.tuple()
        qst_id = relation.itr_parent
        correct = cho_checked == choice.itm_cho_correct
        corr["qst"].setdefault(qst_id, True)
        corr["cho"][cho_id] = correct
        corr["qst"][qst_id] = corr["qst"][qst_id] and correct

    return base.wrap_code("succ", result=corr)
