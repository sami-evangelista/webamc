from webamc.www.all import *
from webamc.db import util as db_util, desc, queries, tables
from webamc.www.admin import router
from webamc.www.db import util as www_db_util


def page(
        ctx: context.Context,
        **kwargs: tp.Unpack[router.args_page_admin_t]
) -> he.Element:
    elements: list[he.Element] = list()

    # list of tables the user can administrate and set the table to show
    tbls = list(queries.get_admin_tables(ctx.dbs, session.usr_id(ctx)))
    tbl_id = kwargs["tbl_id"]
    if tbl_id is None:
        tbl_id = tbls[0].tbl_id

    # get table informations
    tbl_name = tp.cast(tables.Tbl, queries.get_tbl(ctx.dbs, tbl_id)).tbl_name
    tbl = db_util.get_tbl(tbl_name)
    cols = db_util.get_tbl_cols(tbl)

    # select with table names
    opts = [
        he.Option(
            he.Txt(desc.tbl_desc(tbl.tbl_name), fmt=False),
            value=tbl.tbl_id
        )
        for tbl in tbls
    ]
    select_tbls = he.Select(
        *opts,
        name="tbl",
        id_="tbl",
        onchange="admin_table_change()"
    )

    # select with page selection (empty for now)
    select_pages = he.Select(
        he.Option(he.Str("1"), value="1"),
        id_="page_num",
        name="page_num",
        onchange="admin_table_filter()"
    )
    a_prev = he.A(he.Str("<<"), href="javascript:admin_table_navigate(-1)")
    a_next = he.A(he.Str(">>"), href="javascript:admin_table_navigate(+1)")

    # table with all filters
    table_filters = he.Table(
        he.Tr(
            he.Td(he.Txt("name_table")), he.Td(select_tbls)
        ),
        he.Tr(
            he.Td(he.Txt("name_page")), he.Td(a_prev, select_pages, a_next)
        ),
        *[
            he.Tr(
                he.Td(he.Txt(desc.col_desc(col))),
                he.Td(
                    www_db_util.get_col_input_type(ctx, col).element_cmp(),
                    www_db_util.get_col_input_type(ctx, col).element()
                )
            )
            for col in cols
            if www_db_util.is_updatable(col)
        ],
        class_="table-form",
        id_="table-filters",
    )

    # link to filter the table
    a_filter = base.static_img(
        "checkmark",
        "verb_filter",
        js="admin_table_filter()",
        class_="submit"
    )

    # div containing the table and the link
    div_filters = he.Div(
        table_filters,
        a_filter,
        class_="box"
    )
    elements.append(div_filters)

    # empty div containing the table
    div_table_results = he.Div(id_="div-table-body")
    elements.append(div_table_results)

    # javascript to initialize the select with table-id and fill the
    # resulting table
    js = (
        f"$('#tbl').val({json.dumps(tbl_id)});"
        "admin_table_filter();"
    )
    script = he.Script(js)
    elements.append(script)

    return he.ElementList(*elements)
