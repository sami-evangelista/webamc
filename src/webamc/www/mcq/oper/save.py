from webamc.www.all import *
from webamc.db import tables, queries


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:

    active_reg = session.active_registration(ctx)

    # a registration is active => exam mode
    if active_reg is not None:

        reg = active_reg[0]
        sub = queries.get_registration_submission(ctx.dbs, reg)
        assert sub is not None

        # update submission date to now and delete old answers
        sub.sub_date_update = datetime.datetime.now()
        ctx.dbs.query(
            tables.Answer
        ).where(
            tables.Answer.ans_submission == sub.sub_id
        ).delete()
        ctx.dbs.flush()

        # reading the content of the exam from the database and
        # overwrite the one we received from in the request, for
        # security
        args["sub_content"] = types.check_mcq_content(sub.sub_content)

    # no active registration => review mode
    else:

        itm_id = args["itm_id"]
        session.check_can_view_mcq(ctx, itm_id)

        # create review submission linked to user and mcq
        now = datetime.datetime.now()
        sub = tables.Submission(
            sub_type=types.SUBMISSION_TYPE_REVIEW,
            sub_date=now,
            sub_date_update=now,
            sub_visible=True,
            sub_content=json.dumps(args["sub_content"]),
            sub_rev_usr=session.usr_id(ctx),
            sub_rev_mcq=itm_id
        )
        ctx.dbs.add(sub)
        ctx.dbs.flush()

    # save all submission items
    sub_id = sub.sub_id
    for node, _ in types.mcq_enum_items(args["sub_content"]):
        assert node["itm_type"] != types.ITEM_TYPE_CHOICE
        ans = tables.Answer(
            ans_submission=sub_id,
            ans_instance=node["iti_id"]
        )
        ctx.dbs.add(ans)
        if node["itm_type"] == types.ITEM_TYPE_QUESTION:
            cho_ids = {
                i for i, c in args["questions"][node["itm_id"]].items()
                if c
            }
            if len(cho_ids) > 0:
                if node["itm_qst_type"] == types.QUESTION_TYPE_SINGLE:
                    cho_ids = { cho_ids.pop() }
                for cho_id in cho_ids:
                    inst = queries.get_item_instance(
                        ctx.dbs,
                        cho_id,
                        node["iti_num"]
                    )
                    assert inst is not None
                    ans = tables.Answer(
                        ans_submission=sub_id,
                        ans_instance=inst.iti_id
                    )
                    ctx.dbs.add(ans)

    ctx.dbs.commit()

    return base.wrap_code("succ", data={"sub_id": sub_id})
