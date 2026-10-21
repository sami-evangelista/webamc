from itertools import chain

from webamc.www.all import *
from webamc.util import misc
from webamc.db import queries, tables, util as db_util
from webamc.www.db import util as www_db_util
from webamc.www.exam import router


def page(
        ctx: context.Context,
        **kwargs: tp.Unpack[router.args_page_exam_t]
) -> he.Element:
    exams = list(queries.get_usr_exams(ctx.dbs, session.usr_id(ctx)))
    if exams == list():
        return he.Txt("info_no_exam_available")

    elements: list[he.Element] = []
    for item, exam in exams:
        has_registrations = any(
            queries.get_exam_registrations(ctx.dbs, exam.exm_id)
        )

        # link to the exam dashboard
        url = base.mkuri(
            "/exam/page/main",
            sub_page="exam_dashboard",
            exm_id=exam.exm_id
        )
        a_dashboard = base.static_img(
            "list",
            "word_dashboard",
            href=url
        )

        # administration link
        a_admin = base.static_img(
            "mcq",
            "seq_administrate_this_mcq",
            href=base.mkuri(
                "/item/page/main",
                sub_page="item_database",
                itm_id=item.itm_id
            )
        )

        # deletion link (disabled if submission have been made for the
        # exam)
        if has_registrations:
            a_delete = base.static_img(
                "trash",
                "warning_exam_deletion_forbidden",
                class_="warning"
            )
        else:
            a_delete = base.static_img(
                "trash",
                "word_delete",
                js=f"exam_delete({exam.exm_id}, {exam.exm_mcq})"
            )

        # zoom-in/zoom-out link
        a_details = base.static_img(
            "zoom-in",
            "word_details",
            js=f"exam_toggle_details({exam.exm_id})",
            id_=f"img-exam-zoom-{exam.exm_id}"
        )

        # button box
        buttons = [
            a_admin,
            a_dashboard,
            a_delete,
            a_details
        ]
        div_buttons = he.Div(*buttons, class_="submit")

        # div containing details on the exam
        def get_exam_attr(col: types.db_col_t) -> types.db_base_val_t:
            col_name = db_util.get_col_name(col)
            return tp.cast(types.db_base_val_t, getattr(exam, col_name))
        attrs = list()
        for txt, attr in chain(
                www_db_util.get_attributes(
                    ctx,
                    get_exam_attr,
                    tables.Exam.exm_mcq,
                    updatable=False
                ),
                www_db_util.get_attributes(
                    ctx,
                    get_exam_attr,
                    tables.Exam.exm_start,
                    tables.Exam.exm_duration
                )
        ):
            attrs += [txt, attr]
        table_attrs = he.mktable(((e, ) for e in attrs), class_="table-form")
        div_details = he.Div(
            table_attrs,
            id_=f"div-exam-details-{exam.exm_id}",
            style="display: none;",
            class_="exam-details"
        )

        # exam div containing its title, details and buttons
        p_title = he.P(he.Str(str(exam.exm_title)))
        div_exam = he.Div(
            p_title,
            div_details,
            div_buttons,
            class_="box"
        )
        elements.append(div_exam)

    sep: he.Element = he.Br()
    return he.ElementList(*misc.join(sep, elements))
