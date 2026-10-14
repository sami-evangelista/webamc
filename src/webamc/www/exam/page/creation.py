from webamc.www.all import *
from webamc.www.exam import router
from webamc.www.db import util as www_db_util
from webamc.db import tables, util as db_util


def page(
        ctx: context.Context,
        **_: tp.Unpack[router.args_page_exam_t]
) -> he.Element:
    usr_id = session.usr_id(ctx)
    query = ctx.dbs.query(
        tables.Item
    ).where(
        tables.Item.itm_is_mcq
        & (tables.Item.itm_usr == usr_id)
        & (tables.Item.itm_mcq_mode == types.MCQ_MODE_EXAM)
    ).order_by(
        tables.Item.itm_title
    )
    mcq_options = [
        he.Option(
            he.Str(str(item.itm_title)),
            value=str(item.itm_id)
        )
        for item in query
    ]
    if mcq_options == list():
        return he.P(he.Txt("info_no_mcq_available"))

    select_mcq = he.Select(
        *mcq_options,
        id_="exm_mcq"
    ).set_data("type", "integer")
    input_start = www_db_util.html_element(
        ctx, db_util.get_col(tables.Exam.exm_start), prefix=""
    )
    input_duration = www_db_util.html_element(
        ctx, db_util.get_col(tables.Exam.exm_duration), prefix="", val=60
    ).set_attr(
        "size", "4"
    ).set_attr(
        "min", "1"
    )

    table = he.Table(
        he.Tr(
            he.Td(he.Txt("col_desc_exm_mcq")),
            he.Td(select_mcq)
        ),
        he.Tr(
            he.Td(he.Txt("col_desc_exm_start")),
            he.Td(input_start)
        ),
        he.Tr(
            he.Td(he.Txt("col_desc_exm_duration")),
            he.Td(input_duration, he.Txt("word_minutes"))
        ),
        class_="table-form"
    )
    a_send = base.static_img(
        "checkmark", "word_validate", js="exam_submit()", class_="submit"
    )
    result = he.Div(
        table,
        a_send,
        id_="div_creation",
        class_="box"
    )
    return result
