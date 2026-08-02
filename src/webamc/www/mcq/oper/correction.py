import datetime
from webamc.www.all import *
from webamc.db import tables, queries
from webamc.www.mcq import router


def data(
        ctx: context.Context,
        mcq_result: router.args_mcq_result_t
) -> fa.Response:

    mcq_id = mcq_result["mcq_id"]
    session.check_can_view_mcq(ctx, mcq_id)

    usr_id = session.usr_id(ctx)

    # create parent submission entry with current timestamp
    sub = tables.Submission(sub_date=datetime.datetime.now())
    ctx.dbs.add(sub)
    ctx.dbs.flush()
    ctx.dbs.refresh(sub)

    # create review submission linked to user and mcq
    rvs = tables.ReviewSubmission(
        rvs_id=sub.sub_id,
        rvs_usr=usr_id,
        rvs_mcq=mcq_id
    )
    ctx.dbs.add(rvs)
    ctx.dbs.flush()

    # save selected answers for each question
    for qst_id, qst_choices in mcq_result.get("mcq_questions", {}).items():
        qst_id_int = int(qst_id)

        # get default instance (num 1) or fallback to first available
        qst_instance = ctx.dbs.query(tables.ItemInstance).filter_by(
            iti_item=qst_id_int, iti_num=1
        ).first()
        if not qst_instance:
            qst_instance = ctx.dbs.query(tables.ItemInstance).filter_by(
                iti_item=qst_id_int
            ).first()

        if qst_instance:
            ctx.dbs.add(tables.Answer(
                ans_submission=sub.sub_id,
                ans_instance=qst_instance.iti_id
            ))

        # save checked choices
        for cho_id, cho_chosen in qst_choices.items():
            if cho_chosen:
                cho_id_int = int(cho_id)
                cho_instance = ctx.dbs.query(tables.ItemInstance).filter_by(
                    iti_item=cho_id_int, iti_num=1
                ).first()
                if not cho_instance:
                    cho_instance = ctx.dbs.query(tables.ItemInstance).filter_by(
                        iti_item=cho_id_int
                    ).first()

                if cho_instance:
                    ctx.dbs.add(tables.Answer(
                        ans_submission=sub.sub_id,
                        ans_instance=cho_instance.iti_id
                    ))

    # commit all database changes
    ctx.dbs.commit()

    # compute live correction for choices and questions
    corr: dict[tp.Literal["cho", "qst"], dict[int, bool]] = {
        "cho": dict(),
        "qst": dict()
    }
    for cho_id, cho_checked in mcq_result["mcq_choices"].items():
        row = ctx.dbs.query(
            tables.Choice,
            tables.Item
        ).where(
            (tables.Choice.cho_id == int(cho_id))
            & (tables.Choice.cho_id == tables.Item.itm_id)
        ).first()
        assert row is not None
        choice, item = row.tuple()
        cho_correct = bool(choice.cho_correct)
        assert item.itm_parent is not None
        qst_id = int(item.itm_parent)
        correct = cho_checked == cho_correct
        corr["qst"].setdefault(qst_id, True)
        corr["cho"][cho_id] = correct
        corr["qst"][qst_id] = corr["qst"][qst_id] and correct

    response = {
        "success": True,
        "msgs": list(),
        "result": corr
    }
    return fa.responses.JSONResponse(response)