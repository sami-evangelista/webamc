from webamc.www.all import *
from webamc.db import desc, queries, tables, util as db_util
from webamc.www.db import util as www_db_util
from webamc.www.admin import router


def page(
        ctx: context.Context,
        args: router.args_page_table_t
) -> fa.Response:
    session.check_admin_table(ctx, args["tbl_id"])

    elements: list[he.Element] = list()
    row_per_page = 20

    # get table informations
    tbl_name = tp.cast(
        tables.Tbl, queries.get_tbl(ctx.dbs, args["tbl_id"])
    ).tbl_name
    tbl = db_util.get_tbl(tbl_name)
    pkey = db_util.get_tbl_pkey(tbl)
    # cols = [
    #     col
    #     for col in db_util.get_tbl_cols(tbl)
    #     if www_db_util.is_visible(col)
    # ]
    all_tbl_cols = db_util.get_tbl_cols(tbl)

    cols = [
        col
        for col in all_tbl_cols
        if www_db_util.is_visible(col)
    ]



    # table head with column description and new button
    js = "admin_new_row_btn_click()"
    img_new = base.static_img("add", "seq_new_row", js=js)
    tds = [he.Td(he.Txt(desc.col_desc(col))) for col in cols]
    tds.append(he.Td(img_new))
    thead = he.Thead(he.Tr(*tds))
    trs = list()

    # hidden row containing input fields for a new record
    inputs = {
        col.name: www_db_util.html_element(ctx, col, prefix="new-")
        for col in cols
        if www_db_util.is_updatable(col)
    }
    tds = [
        he.Td(
            he.ElementList(*inputs[col.name])
            if col.name in inputs else he.Empty()
        )
        for col in cols
    ]
    img_add = base.static_img(
        "checkmark",
        "verb_create",
        js="admin_add_row(tbl_name, tbl_cols)"
    )
    tds.append(he.Td(img_add))
    tr_add = he.Tr(
        *tds,
        id_="tr_new_row",
        style="display: none;"
    )
    trs.append(tr_add)

    # create the query to select and count rows
    wheres = www_db_util.get_filter_wheres(tbl, args["filters"])
    query = ctx.dbs.query(tbl).where(sa.and_(*wheres))
    query_count = query.statement.with_only_columns(  # type: ignore
        sa.func.count(pkey) # pylint: disable=not-callable
    ).order_by(None)
    nrows = int(ctx.dbs.execute(query_count).scalar())  # type: ignore
    start = (args["page_num"] - 1) * row_per_page
    if start >= nrows:
        start = 0
        args["page_num"] = 1
    query = query.offset(
        (args["page_num"] - 1) * row_per_page
    ).limit(
        row_per_page
    )

    # update the page select with the actual number of pages
    npages = max(1, math.ceil(nrows / row_per_page))
    opts = [
        he.Option(he.Str(str(n + 1)), value=str(n + 1))
        for n in range(npages)
    ]
    options_pages = he.ElementList(*opts)

    # create some JS variables and initialise page_num select now we
    # know the number of records in the table
    col_names = {col: inp[0]["name"] for col, inp in inputs.items()}
    js = "\n".join([
        f"var tbl_name = {json.dumps(tbl_name)};",
        f"var tbl_cols = {json.dumps(col_names)};",
        f"$('#page_num').html({json.dumps(str(options_pages))});",
        f"$('#page_num').val({json.dumps(args['page_num'])});"
    ])
    script = he.Script(js)
    elements.append(script)

    # one row per result
    for row in query.all():
        def get_val(col_name: str) -> types.db_base_val_t:
            return tp.cast(types.db_base_val_t, getattr(row, col_name))
        attrs = www_db_util.get_attributes(
            ctx, [c.name for c in cols], get_val
        )
        tds = [he.Td(attr) for _, attr in attrs]
        pkey_val = getattr(row, pkey.name)
        js = f"admin_delete_row('{tbl_name}', '{pkey.name}', {pkey_val})"
        img = base.static_img("trash", "verb_delete", js=js)
        tds.append(he.Td(img))
        trs.append(he.Tr(*tds))

    elements.append(
        he.P(he.Txt("seq_records_found"), he.Str(f": {nrows}"))
    )

    p = he.P(he.Table(thead, *trs, class_="solid-table"))
    elements.append(p)

    return fa.responses.HTMLResponse(str(he.ElementList(*elements)))
