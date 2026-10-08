from webamc.www.all import *
from webamc.db import util as db_util, desc
from webamc.www.db import util as www_db_util
from webamc.www.item import router


def page(
        ctx: context.Context,
        **kwargs: tp.Unpack[router.args_page_item_t]
) -> he.Element:

    # type
    itm_types = [
        (he.Txt("name_mcq"), "mcq"),
        (he.Txt("name_exercise"), "exe"),
        (he.Txt("name_question"), "qst")
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
        "checkmark", "verb_filter", js="item_filter()", class_="submit"
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
        for col in db_util.get_tbl_cols("item")
        if www_db_util.is_visible(col)
    ]
    table = he.Table(
        he.Tr(he.Td(he.Txt("name_type")), he.Td(select_type)),
        *trs,
        he.Tr(he.Td(he.Txt("name_tags")), he.Td(div_tags)),
        class_="table-form",
        id_="table-item-filters"
    )
    js = f"item_filters_init({json.dumps(div_tags_id)})"
    div_filters = he.Div(
        table,
        a_filter,
        he.Script(js),
        style="position: relative;",
        class_="box"
    )

    script = he.Script(f"item_filter({json.dumps(kwargs.get('itm_id'))});")
    elements = [
        div_filters,
        he.Div(id_="div-item-list"),
        script
    ]
    return he.ElementList(*elements)
