from webamc.www.all import *
from webamc.db import tables, queries
from webamc.www.db import util as www_db_util


def page(ctx: context.Context, filters: dict[str, tp.Any]) -> fa.Response:

    # build the request to select items
    where = [
        tables.Item.itm_usr == session.usr_id(ctx),
        (tables.Item.itm_standalone == True)
        | (tables.Item.itm_parent == None)
    ]
    where += www_db_util.get_filter_wheres("item", filters)
    try:
        where += {
            "mcq": [
                tables.Item.itm_id == tables.Mcq.mcq_id
            ],
            "qst": [
                tables.Item.itm_type == types.ITEM_TYPE_QUESTION
            ]
        }[filters.get("itm_type", "mcq")]
        itm_id = filters.get("itm_id")
        if itm_id is not None:
            where.append(tables.Item.itm_id == itm_id)
        tags = filters.get("itm_tags", list())
        if tags != list():
            sub_queries = [
                ctx.dbs.query(
                    tables.ItemTag.itg_item
                ).where(
                    tables.ItemTag.itg_tag == tag_id
                )
                for tag_id in tags
            ]
            where += [
                tables.Item.itm_id.in_(sub_query)
                for sub_query in sub_queries
            ]
    except (KeyError, ValueError):
        raise fa.HTTPException(status_code=500)

    items = ctx.dbs.query(
        tables.Item
    ).where(
        sa.and_(*where)
    ).order_by(
        tables.Item.itm_code
    ).all()
    elements = [div_item(ctx, item) for item in items]
    p = he.P(he.Txt("seq_items_found"), he.Str(f": {len(elements)}"))
    div = he.Div(*elements)

    # if there is only item returned by the query, load it
    if len(items) == 1:
        script: he.Element = he.Script(
            f"item_admin_code_click({items[0].itm_id})"
        )
    else:
        script = he.Empty()
    body = he.ElementList(p, div, script)
    return fa.responses.HTMLResponse(str(body))


def div_item(ctx: context.Context, item: tables.Item) -> he.Element:

    mcq = queries.get_item_mcq(ctx.dbs, item.itm_id)
    div_body_id = f"div-item-body-{item.itm_id}"

    nb_instances = len(
        queries.get_instances(ctx.dbs, item.itm_id)
    )
    badge = ""
    if nb_instances > 1:
        badge = f" ({nb_instances} var.)"

    # <p> containing item code
    if mcq is not None:
        label = he.Txt("name_mcq")
        p_code_class = "code code-mcq"
    elif item.itm_type == types.ITEM_TYPE_QUESTION:
        label = he.Txt("name_question")
        p_code_class = "code code-question"
    else:
        label = he.Txt("name_exercise")
        p_code_class = "code code-exercise"

    p_code = he.P(
        label,
        he.Str(f" [{item.itm_code}]{badge}"),
        class_=p_code_class,
        onclick=f"item_admin_code_click({item.itm_id})"
    )

    # <div> containing the item body
    div_body = he.Div(
        id_=div_body_id
    )

    return he.ElementList(
        p_code,
        div_body
    )
