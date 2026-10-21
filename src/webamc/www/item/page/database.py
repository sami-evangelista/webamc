from webamc.www.all import *
from webamc.db import util as db_util, desc, tables
from webamc.www.db import util as www_db_util


def page(
        ctx: context.Context,
        **kwargs: tp.Unpack[types.args_route_item_item_t]
) -> he.Element:

    # type
    itm_types = [
        (he.Txt("word_mcq"), "mcq"),
        (he.Txt("word_exercise"), "exe"),
        (he.Txt("word_question"), "qst")
    ]
    select_type = he.Select(
        *[he.Option(lbl, value=typ) for lbl, typ in itm_types],
        id_="itm_type",
        name="itm_type",
    )

    # tags
    div_tags_id = "div_tags_filter"
    div_tags = he.Div(id_=div_tags_id)

    # filter button
    a_filter = base.static_img(
        "checkmark", "word_filter", js="item_db_filter()", class_="submit"
    )

    # table containing all filters
    def get_inputs(col: sa.Column[tp.Any]) -> tuple[he.Element, he.Element]:
        input_type = www_db_util.get_col_input_type(ctx, col)
        return (input_type.element_cmp(), input_type.element())
    trs = [
        he.Tr(
            he.Td(he.Txt(desc.col_desc(col))),
            he.Td(*get_inputs(col))
        )
        for col in db_util.get_tbl_visible_cols(tables.Item)
    ]
    table = he.Table(
        he.Tr(he.Td(he.Txt("word_type")), he.Td(select_type)),
        *trs,
        he.Tr(he.Td(he.Txt("word_tags")), he.Td(div_tags)),
        class_="table-form",
        id_="table-item-filters"
    )
    js = f"item_db_filters_init({json.dumps(div_tags_id)})"
    div_filters = he.Div(
        table,
        a_filter,
        he.Script(js),
        style="position: relative;",
        class_="box"
    )

    itm_id = kwargs.get("itm_id")
    script = he.Script(f"item_db_filter({json.dumps(itm_id)});")
    elements = [
        div_filters,
        he.Div(id_="div-item-list"),
        script
    ]
    return he.ElementList(*elements)
