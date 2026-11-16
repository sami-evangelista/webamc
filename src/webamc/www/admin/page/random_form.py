from webamc.www.all import *


def page(ctx: context.Context, tbl_id: tp.Optional[int]) -> he.Element:

    if not session.is_root(ctx):
        raise fa.HTTPException(status_code=403)

    input_no_exams = he.Input(
        type_="number",
        size="4",
        id_="no_rnd_exams",
        value="10"
    ).set_data(
        "type", "integer"
    )
    input_no_submissions = he.Input(
        type_="number",
        size="4",
        id_="no_rnd_submissions",
        value="100"
    ).set_data(
        "type", "integer"
    )
    trs = [
        (he.Txt("admin_no_exams"), input_no_exams),
        (he.Txt("admin_no_submissions"), input_no_submissions)
    ]
    table = he.mktable(trs, class_="table-form")
    a_submit = base.static_img(
        "checkmark",
        "base_send",
        js="admin_submit_random()",
        class_="submit"
    )
    result = he.Div(
        table,
        a_submit,
        class_="box",
        id_="div-random-form"
    )
    return result
