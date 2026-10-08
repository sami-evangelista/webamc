from webamc.www.all import *
from webamc.db import tables, queries
from webamc.www.db import util as www_db_util


def page(ctx: context.Context, filters: dict[str, tp.Any]) -> fa.Response:

    # build the request to select items
    where = [
        tables.Item.itm_usr == session.usr_id(ctx)
    ]
    itm_id = filters.get("itm_id")
    if itm_id is not None:
        where.append(tables.Item.itm_id == itm_id)
    else:
        where += www_db_util.get_filter_wheres("item", filters)
        where += {
            "mcq": [
                tables.Item.itm_id == tables.Mcq.mcq_id
            ],
            "qst": [
                tables.Item.itm_type == types.ITEM_TYPE_QUESTION,
                tables.Item.itm_id == tables.Question.qst_id
            ],
            "exe": [
                tables.Item.itm_type == types.ITEM_TYPE_EXERCISE,
                tables.Item.itm_id == tables.Exercise.exe_id
            ]
        }[filters.get("itm_type", "mcq")]
        itm_id = filters.get("itm_id")
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

    items = ctx.dbs.query(
        tables.Item
    ).where(
        sa.and_(*where)
    ).order_by(
        tables.Item.itm_code
    ).all()
    elements = [div_item(ctx, item, None) for item in items]

    if not filters.get("display_num_found", True):
        p = he.P(he.Str("&nbsp;", escape=False))
    else:
        p = he.P(he.Txt("param_seq_items_found", args=(str(len(elements)), )))

    # if there is only one item returned by the query, load it
    if len(items) == 1:
        script: he.Element = he.Script(
            f"item_admin_code_click({items[0].itm_id}, false, null)"
        )
    else:
        script = he.Empty()
    body = he.ElementList(p, *elements, script)
    return fa.responses.HTMLResponse(str(body))


def div_item(
        ctx: context.Context,
        item: tables.Item,
        item_parent: None | tables.Item
) -> he.Element:

    mcq = queries.get_item_mcq(ctx.dbs, item.itm_id)
    div_code_id = f"div-item-code-{item.itm_id}"
    div_body_id = f"div-item-body-{item.itm_id}"

    # <div> containing item code
    if mcq is not None:
        label = he.Txt("name_mcq")
        div_code_class = "item-code item-code-mcq"
    elif item.itm_type == types.ITEM_TYPE_QUESTION:
        label = he.Txt("name_question")
        div_code_class = "item-code item-code-question"
    else:
        label = he.Txt("name_exercise")
        div_code_class = "item-code item-code-exercise"
    buttons: list[he.Element] = list()
    if item_parent is not None and session.has_admin_right(ctx, item_parent):
        img_unlink = base.static_img(
            "unlink",
            "verb_detach",
            js=f"item_detach({item.itm_id});"
        )
        buttons.append(img_unlink)
    if session.has_admin_right(ctx, item):
        img_delete = base.static_img(
            "trash",
            "verb_delete",
            js=f"item_delete({item.itm_id});"
        )
        buttons.append(img_delete)
    if len(buttons) == 0:
        div_button: he.Element = he.Empty()
    else:
        div_button = he.Div(
            *buttons,
            class_="item-box-buttons"
        )
    is_root = item_parent is None
    p_code = he.P(
        label,
        he.Str(f" [{item.itm_code}]"),
        style="cursor: pointer;",
        onclick=(
            "item_admin_code_click("
            f"{item.itm_id}, {json.dumps(is_root)}, null)"
        )
    )
    div_code = he.Div(
        p_code,
        div_button,
        id_=div_code_id,
        class_=div_code_class
    )

    # <div> containing the item body (initialised empty as it is not
    # loaded yet)
    div_body = he.Div(
        id_=div_body_id
    )

    return he.ElementList(
        div_code,
        div_body
    )
