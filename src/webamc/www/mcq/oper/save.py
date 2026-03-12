#!/usr/bin/env python3

from webamc.www.all import *
from webamc.db import tables
from webamc.www.mcq import router


def data(
        ctx: context.Context,
        mcq_result: router.args_mcq_result_t
) -> fa.Response:

    session.check_active_registration(ctx)
    active_registration = session.active_registration(ctx)
    assert active_registration is not None
    registration, exam, mcq = active_registration
    usr_id = session.usr_id(ctx)
    mcq_id = mcq_result["mcq_id"]
    exam_sub = ctx.dbs.query(tables.ExamSubmission).where(
        (tables.ExamSubmission.exs_registration == registration.reg_id)
    ).scalar()

    # set submission update to now and delete old answers
    exam_sub.sub_date_update = datetime.datetime.now()
    ctx.dbs.query(
        tables.Answer
    ).where(
        tables.Answer.ans_submission==exam_sub.sub_id
    ).delete()
    ctx.dbs.flush()

    # insert new answers
    for qst_id, qst_choices in mcq_result["mcq_questions"].items():
        ans = tables.Answer(
            ans_submission=exam_sub.sub_id,
            ans_item=qst_id
        )
        ctx.dbs.add(ans)
        for cho_id, cho_chosen in qst_choices.items():
            if cho_chosen:
                ans = tables.Answer(
                    ans_submission=exam_sub.sub_id,
                    ans_item=cho_id
                )
                ctx.dbs.add(ans)
    response = {
        "success": True,
        "msgs": list(),
        "result": None
    }
    return fa.responses.JSONResponse(response)
