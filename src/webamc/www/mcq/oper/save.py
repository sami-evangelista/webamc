from webamc.www.all import *
from webamc.db import tables, queries


def data(
        ctx: context.Context,
        mcq_result: types.args_route_mcq_result_t
) -> fa.Response:

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

    # reading the content of exam
    content_tree = json.loads(sub.sub_exm_content)
    itm_to_itinum = {}

    # private function to map all the answers. it saves the question
    # id with the instance num in a dict
    def map_instances(node: dict[str, tp.Any]) -> None:
        if "iti_num" in node:
            itm_to_itinum[node["itm_id"]] = node["iti_num"]
        if "itm_children" in node:
            for child in node["itm_children"]:
                map_instances(child)

    map_instances(content_tree)

    # insert new answers
    for qst_id, qst_choices in mcq_result["questions"].items():

        # get the instance num with the question id
        iti_num = itm_to_itinum.get(qst_id, 1)

        # finding the instance id with the question id and instance num
        qst_instance = queries.get_item_instance(
            ctx.dbs,
            qst_id,
            iti_num
        )
        if qst_instance is not None:
            ans = tables.Answer(
                ans_submission=sub.sub_id,
                ans_instance=qst_instance.iti_id
            )
            ctx.dbs.add(ans)
        for cho_id, cho_chosen in qst_choices.items():
            if cho_chosen:
                cho_instance = queries.get_item_instance(
                    ctx.dbs,
                    cho_id,
                    iti_num
                )
                if cho_instance is not None:
                    ans = tables.Answer(
                        ans_submission=sub.sub_id,
                        ans_instance=cho_instance.iti_id
                    )
                    ctx.dbs.add(ans)
    return base.wrap_code("succ")
