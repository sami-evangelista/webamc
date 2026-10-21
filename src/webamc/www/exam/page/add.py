from webamc.www.all import *
from webamc.www.exam import router
from webamc.www.db import util as www_db_util
from webamc.db import tables, util as db_util, desc


def page(
        ctx: context.Context,
        **_: tp.Unpack[router.args_page_exam_t]
) -> he.Element:
    usr_id = session.usr_id(ctx)
    where = [
        tables.Item.itm_is_mcq
        & (tables.Item.itm_usr == usr_id)
        & (tables.Item.itm_mcq_mode == types.MCQ_MODE_EXAM)
    ]
    txt_mcq = base.field_label(desc.col_txt(tables.Exam.exm_mcq))
    input_mcq = db_util.get_col_type(
        tables.Exam.exm_mcq
    ).get_input(
        db_util.get_col(tables.Exam.exm_mcq),
        dbs=ctx.dbs,
        where=where
    ).element()
    if input_mcq.children == list():
        return he.P(he.Txt("info_no_mcq_available"))

    txt_title, input_title = next(
        x for x in www_db_util.get_txt_and_input(ctx, tables.Exam.exm_title)
    )
    txt_start, input_start = next(
        x for x in www_db_util.get_txt_and_input(ctx, tables.Exam.exm_start)
    )
    txt_duration, input_duration = next(
        x for x in www_db_util.get_txt_and_input(ctx, tables.Exam.exm_duration)
    )
    input_duration.set_attr("size", "4")
    input_duration.set_attr("min", "1")
    input_duration.set_attr("value", "60")

    elements = [
        txt_title, input_title,
        txt_mcq, input_mcq,
        txt_start, input_start,
        txt_duration, input_duration
    ]

    table = he.mktable(((e, ) for e in elements), class_="table-form")
    a_send = base.static_img(
        "checkmark",
        "word_validate",
        js="exam_submit()",
        class_="submit"
    )
    result = he.Div(
        table,
        a_send,
        id_="div_creation",
        class_="box"
    )
    return result
