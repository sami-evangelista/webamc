from webamc.www.all import *
from webamc.db import tables, queries


def _save_submission(
        ctx: context.Context,
        sub_id: int,
        args: types.args_oper_t
) -> None:
    mcq_content = args["content"]
    for node, _ in types.mcq_enum_items(mcq_content):
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


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:

    session.check_active_registration(ctx)
    active_registration = session.active_registration(ctx)
    assert active_registration is not None
    registration = active_registration[0]
    sub = queries.get_registration_submission(ctx.dbs, registration)
    assert sub is not None
    assert sub.sub_exm_content is not None

    # set submission update to now and delete old answers
    sub.sub_exm_date_update = datetime.datetime.now()
    ctx.dbs.query(
        tables.Answer
    ).where(
        tables.Answer.ans_submission == sub.sub_id
    ).delete()
    ctx.dbs.flush()

    # reading the content of the exam from the database and overwrite
    # the one we received from in the request, for security
    args["content"] = json.loads(sub.sub_exm_content)

    _save_submission(ctx, sub.sub_id, args)

    return base.wrap_code("succ")
