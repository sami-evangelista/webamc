from webamc.www.all import *
from webamc.db import tables, queries


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:

    filters = args["stat_filters"]
    output_data = filters["output_data"]

    # create the query to get (submission, usr) we will look at
    query_mcqs = ctx.dbs.query(
        tables.Submission,
        tables.Usr
    ).where(
        (tables.Item.itm_id == tables.Submission.sub_rev_mcq)
        & (tables.Item.itm_usr == session.usr_id(ctx))
        & (tables.Submission.sub_rev_usr == tables.Usr.usr_id)
    )
    query_exams = ctx.dbs.query(
        tables.Submission,
        tables.Usr
    ).where(
        (tables.Registration.reg_exam == tables.Exam.exm_id)
        & (tables.Exam.exm_mcq == tables.Item.itm_id)
        & (tables.Item.itm_usr == session.usr_id(ctx))
        & (tables.Registration.reg_usr == tables.Usr.usr_id)
        & (tables.Submission.sub_exm_registration ==
           tables.Registration.reg_id)           
    )
    if filters["usr_id"] is not None:
        query_mcqs = query_mcqs.where(
            tables.Usr.usr_id == filters["usr_id"]
        )
        query_exams = query_exams.where(
            tables.Usr.usr_id == filters["usr_id"]
        )
    if filters["itm_id"] is not None:
        query_mcqs = query_mcqs.where(
            tables.Item.itm_id == filters["itm_id"]
        )
        query_exams = query_exams.where(
            tables.Item.itm_id == filters["itm_id"]
        )
    if filters["exm_id"] is not None:
        query_exams = query_exams.where(
            tables.Exam.exm_id == filters["exm_id"]
        )
    if filters["exm_id"] is not None:
        query = query_exams
    else:
        query = query_mcqs.union(query_exams)

    # get results for all these submissions
    sub_usr = {
        sub: usr for sub, usr in query
    }
    sub_result = queries.get_submissions_result(
        ctx.dbs, (sub.sub_id for sub in sub_usr)
    )

    obj_t = tp.Union[tables.Usr, tables.Item]
    no_occ: dict[obj_t, int] = dict()
    values: dict[obj_t, float] = dict()
    for sub_id, subres in sub_result.items():
        if output_data == "user":
            usr = sub_usr[subres["sub"]]
            no_occ.setdefault(usr, 0)
            values.setdefault(usr, 0)
            for item, score in subres["score"].items():
                if item.itm_is_mcq:
                    no_occ[usr] += 1
                    ratio = float(score) / float(subres["max_score"][item])
                    values[usr] += ratio
        elif output_data in ("question", "exercise", "mcq"):
            def cond(item: tables.Item) -> bool:
                if output_data == "mcq":
                    return item.itm_is_mcq
                elif output_data == "question":
                    return item.itm_type == types.ITEM_TYPE_QUESTION
                return not item.itm_is_mcq and item.itm_type in {
                    types.ITEM_TYPE_EXERCISE,
                    types.ITEM_TYPE_PACK
                }
            for item, score in subres["score"].items():
                if cond(item):
                    no_occ.setdefault(item, 0)
                    values.setdefault(item, 0)
                    no_occ[item] += 1
                    ratio = float(score) / float(subres["max_score"][item])
                    values[item] += ratio

    def get_label(obj: obj_t) -> str:
        if isinstance(obj, tables.Usr):
            return obj.fmt()
        elif isinstance(obj, tables.Item):
            return str(obj.itm_code)
        assert False

    no_occ = {k: v for k, v in no_occ.items() if v > 0}
    objs: list[obj_t] = sorted(no_occ.keys(), key=get_label)
    chart_labels = [get_label(o) for o in objs]
    chart_values = [values[o] / no_occ[o] for o in objs]

    def key(cmp_val: tuple[str, float]) -> tp.Any:
        sort_by = filters["sort_by"]
        if sort_by in ("name-asc", "name-desc"):
            return cmp_val[0], cmp_val[1]
        return cmp_val[1], cmp_val[0]
        
    zipped = sorted(
        zip(chart_labels, chart_values),
        key=key,
        reverse=filters["sort_by"] in ("score-desc", "name-desc")
    )

    data = {
        "type": "bar",
        "data": {
            "labels": [c[0] for c in zipped],
            "datasets": [
                {
                    "data": [c[1] for c in zipped]
                }
            ]
        },
        "options": {
            "legend": {
                "display": False
            },
            "responsive": True,
            "plugins": {
                "title": {
                    "display": True,
                    "text": "Min and Max Settings"
                }
            },
            "scales": {
                "y": {
                    "min": 0,
                    "max": 1
                }
            }
        }
    }
    return base.wrap_code("succ", data=data)
