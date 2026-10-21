import datetime

from webamc.db import tables, queries
from webamc.www.all import *


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

    # save selected answers for each question
    for qst_id, qst_choices in mcq_result.get("questions", dict()).items():
        qst_id_int = int(qst_id)

        # get default instance (num 1) or fallback to first available
        qst_instance = queries.get_item_instance(ctx.dbs, qst_id_int, 1)
        if qst_instance is None:
            qst_instance = ctx.dbs.query(
                tables.ItemInstance
            ).filter_by(
                iti_item=qst_id_int
            ).first()

        if qst_instance is not None:
            ans = tables.Answer(
                ans_submission=sub.sub_id,
                ans_instance=qst_instance.iti_id
            )
            ctx.dbs.add(ans)

        # save checked choices
        for cho_id, cho_chosen in qst_choices.items():
            if cho_chosen:
                cho_id_int = int(cho_id)
                cho_instance = queries.get_item_instance(
                    ctx.dbs,
                    cho_id_int,
                    1
                )
                if cho_instance is None:
                    cho_instance = ctx.dbs.query(
                        tables.ItemInstance
                    ).filter_by(
                        iti_item=cho_id_int
                    ).first()

                if cho_instance:
                    ans = tables.Answer(
                        ans_submission=sub.sub_id,
                        ans_instance=cho_instance.iti_id
                    )
                    ctx.dbs.add(ans)

    # commit all database changes
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
