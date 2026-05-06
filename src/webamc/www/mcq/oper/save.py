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
    exam_sub.exs_date_update = datetime.datetime.now()
    ctx.dbs.query(
        tables.Answer
    ).where(
        tables.Answer.ans_submission == exam_sub.exs_id
    ).delete()
    ctx.dbs.flush()

    # reading the content of exam
    content_tree = json.loads(exam_sub.exs_content)
    itm_to_itinum = {}
    
    # private function to map all the answers
    # it's save the question id with the instance num in a dict
    def map_instances(node):
        if "iti_num" in node:
            itm_to_itinum[node["itm_id"]] = node["iti_num"]
        if "itm_children" in node:
            for child in node["itm_children"]:
                map_instances(child)
                
    map_instances(content_tree)
    # ----------------------------------------------------------------------

    # insert new answers
    for qst_id, qst_choices in mcq_result["mcq_questions"].items():
        # get the instance num with the question id
        iti_num = itm_to_itinum.get(qst_id, 1)
        
        # finding the instance id with the question id and instance num
        qst_instance = ctx.dbs.query(tables.ItemInstance).filter_by(
            iti_item=qst_id, iti_num=iti_num
        ).first()
        
        if qst_instance:
            ans = tables.Answer(
                ans_submission=exam_sub.exs_id,
                ans_instance=qst_instance.iti_id 
            )
            ctx.dbs.add(ans)
            
        for cho_id, cho_chosen in qst_choices.items():
            if cho_chosen:
                cho_instance = ctx.dbs.query(tables.ItemInstance).filter_by(
                    iti_item=cho_id, iti_num=iti_num
                ).first()
                
                if cho_instance:
                    ans = tables.Answer(
                        ans_submission=exam_sub.exs_id,
                        ans_instance=cho_instance.iti_id 
                    )
                    ctx.dbs.add(ans)
                    
    response = {
        "success": True,
        "msgs": list(),
        "result": None
    }
    return fa.responses.JSONResponse(response)