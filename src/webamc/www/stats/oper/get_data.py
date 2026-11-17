from webamc.www.all import *
from webamc.db import tables, queries
from webamc.util import fmt


def data(ctx: context.Context, args: types.args_oper_t) -> fa.Response:

    filters = args["stat_filters"]
    output_data = filters["output_data"]

    # create the query to get (submission, usr, exam) we will look at
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
        tables.Usr,
        tables.Exam
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

    # get results for all these submissions
    subs: dict[
        tables.Submission,
        tuple[tables.Usr, tp.Optional[tables.Exam]]
    ] = {
        sub: (usr, exam) for sub, usr, exam in query_exams
    }
    if filters["exm_id"] is None and output_data != "exam":
        subs = {
            **subs,
            **{sub: (usr, None) for sub, usr in query_mcqs}
        }
    subs_result = queries.get_submissions_result(
        ctx.dbs, (sub.sub_id for sub in subs)
    )

    obj_t = tp.Union[tables.Exam, tables.Usr, tables.Item]
    no_occ: dict[obj_t, int] = dict()
    values: dict[obj_t, float] = dict()
    legends: dict[obj_t, list[tuple[datetime.datetime, str]]] = dict()

    def new_obj(o: obj_t) -> None:
        no_occ.setdefault(o, 0)
        values.setdefault(o, 0)
        legends.setdefault(o, list())

    def new_sub(
            o: obj_t,
            score: int,
            max_score: int,
            usr: tables.Usr,
            sub: tables.Submission
    ) -> None:
        no_occ[o] += 1
        values[o] += float(score) / float(max_score)
        legends[o].append((sub.sub_date_update, usr.fmt()))

    for subres in subs_result.values():
        sub = subres["sub"]
        usr, exam = subs[sub]
        if output_data == "user":
            new_obj(usr)
            for item, score in subres["score"].items():
                if item.itm_is_mcq:
                    new_sub(usr, score, subres["max_score"][item], usr, sub)
        elif output_data in ("exam", "question", "exercise", "mcq"):
            def cond(item: tables.Item) -> bool:
                if output_data in ("exam", "mcq"):
                    return item.itm_is_mcq
                if output_data == "question":
                    return item.itm_type == types.ITEM_TYPE_QUESTION
                return not item.itm_is_mcq and item.itm_type in {
                    types.ITEM_TYPE_EXERCISE,
                    types.ITEM_TYPE_PACK
                }
            for item, score in subres["score"].items():
                if cond(item):
                    if output_data != "exam":
                        o: obj_t = item
                    else:
                        assert exam is not None
                        o = exam
                    new_obj(o)
                    new_sub(o, score, subres["max_score"][item], usr, sub)

    def get_label(obj: obj_t) -> str:
        if isinstance(obj, tables.Usr):
            return obj.fmt()
        if isinstance(obj, tables.Item):
            if obj.itm_title is not None:
                return obj.itm_title
            return str(obj.itm_code)
        if isinstance(obj, tables.Exam):
            return str(obj.exm_title)
        assert False

    no_occ = {k: v for k, v in no_occ.items() if v > 0}
    objs: list[obj_t] = sorted(no_occ.keys(), key=get_label)

    # sort values returned
    def key(cmp_val: tuple[obj_t, str, float, str]) -> tp.Any:
        if filters["sort_key"] == "name":
            return cmp_val[1], cmp_val[2]
        return cmp_val[2], cmp_val[1]
    def legend_to_element(
            submissions: list[tuple[datetime.datetime, str]]
    ) -> str:
        def fmt_legend(legend: tuple[datetime.datetime, str]) -> str:
            return fmt.fmt_datetime(legend[0]) + " - " + legend[1]
        submissions = sorted(submissions)
        elements = he.ElementList(
            he.Txt("stats_param_no_submissions_found", str(len(submissions))),
            he.Ul(*(he.Li(he.Str(fmt_legend(sub))) for sub in submissions))
        )
        return str(elements)

    zipped = sorted(
        zip(
            objs,
            (get_label(o) for o in objs),
            (values[o] / no_occ[o] for o in objs),
            (legend_to_element(legends[o]) for o in objs)
        ),
        key=key,
        reverse=filters["sort_order"] == "desc"
    )

    # create image links
    def get_img(o: obj_t) -> tp.Optional[str]:
        if isinstance(o, tables.Item):
            iti = ctx.dbs.query(
                tables.ItemInstance
            ).where(
                (tables.ItemInstance.iti_item == o.itm_id)
                & (tables.ItemInstance.iti_img.is_not(None))
            ).order_by(
                tables.ItemInstance.iti_num
            ).first()
            if iti is not None:
                img = he.Img(
                    src=base.img_src(ctx, iti.iti_id, iti.iti_uuid),
                    alt=str(o.itm_code)
                )
                return str(img)
        return None
    imgs = [get_img(c[0]) for c in zipped]

    response_data = {
        "imgs": imgs,
        "labels": [c[1] for c in zipped],
        "data": [100 * c[2] for c in zipped],
        "legends": [c[3] for c in zipped]
    }
    return base.wrap_code("succ", data=response_data)
