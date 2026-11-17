from webamc.db import queries
from webamc.www.all import *
from webamc.www import session
from webamc.www.exam import util as www_exam_util


def page(ctx: context.Context) -> fa.Response:

    grps = set(
        g.grp_id for g in queries.get_submit_grps(ctx.dbs, session.usr_id(ctx))
    )

    # div with filters
    _, select_exam = www_exam_util.get_exams_select(ctx)
    select_usr = www_exam_util.get_usrs_select(ctx, grps)
    select_mcq = www_exam_util.get_items_select(ctx, is_mcq=True)
    trs = [
        (he.Txt("base_exam"), select_exam),
        (he.Txt("base_mcq"), select_mcq),
        (he.Txt("base_usr"), select_usr)
    ]
    table_filters = he.mktable(
        trs,
        class_="table-form"
    )
    div_filters = he.Div(
        he.H2(he.Txt("base_filters"), style="text-align: center"),
        table_filters,
        style="min-width: 600px"
    )

    # div with output
    select_data = he.Select(
        he.Option(he.Txt("base_question"), value="question"),
        he.Option(he.Txt("base_exercise"), value="exercise"),
        he.Option(he.Txt("base_mcq"), value="mcq"),
        he.Option(he.Txt("base_exam"), value="exam"),
        he.Option(he.Txt("base_usr"), value="user"),
        id_="output_data"
    )
    select_sort_by = he.Select(
        he.Option(he.Txt("stats_sort_by_name"), value="name"),
        he.Option(he.Txt("stats_sort_by_score"), value="score"),
        id_="sort_key"
    )
    select_sort_order = he.Select(
        he.Option(he.Txt("stats_sort_asc"), value="asc"),
        he.Option(he.Txt("stats_sort_desc"), value="desc"),
        id_="sort_order"
    )
    trs = [
        (he.Txt("stats_data_outputted"), select_data),
        (he.Txt("stats_sort_by"), select_sort_by),
        (he.Txt("stats_sort_order"), select_sort_order)
    ]
    table_outputs = he.mktable(
        trs,
        class_="table-form"
    )
    div_output = he.Div(
        he.H2(he.Txt("base_output"), style="text-align: center"),
        table_outputs,
        style="min-width: 600px"
    )

    # main inputs div
    a_create = base.static_img(
        "checkmark",
        "base_send",
        js="stats_send()",
        class_="submit"
    )
    div_inputs = he.Div(
        div_filters,
        he.Div(style="width: 50px;"),  # separator div
        div_output,
        a_create,
        class_="box",
        id_="stats-div-inputs",
        style="display: flex;"
    )

    # canvas
    canvas = he.Canvas(
        id_="stats-canvas-chart"
    )
    div_canvas = he.Div(
        canvas,
        id_="stats-div-chart-container"
    )
    script = he.Script("stats_init()")

    # legend
    div_legend = he.Div(
        id_="stats-div-legend"
    )

    body = he.ElementList(div_inputs, div_canvas, div_legend, script)
    return base.page(ctx, "stats", body)
