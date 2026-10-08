from webamc.www.all import *
from webamc.db import tables, desc, queries
from webamc.www.db import util as www_db_util
from . import database_list


def page(
        ctx: context.Context,
        itm_id: int,
        iti_num: int
) -> fa.Response:

    owner = queries.get_item_owner(ctx.dbs, itm_id)
    if owner is None or owner.usr_id != session.usr_id(ctx):
        raise fa.HTTPException(status_code=403)

    item = queries.get_item(ctx.dbs, itm_id)
    mcq = queries.get_item_mcq(ctx.dbs, item.itm_id)
    all_instances = queries.get_instances(ctx.dbs, item.itm_id)

    table_tags_id = f"table-item-tags-{item.itm_id}"
    div_body_id = f"div-item-body-{item.itm_id}"

    # <tr> containing attributes
    trs: list[he.Tr] = list()

    # select item columns to show
    cols = ["itm_title", "itm_date"]
    cols += {
        types.ITEM_TYPE_PACK: list(),
        types.ITEM_TYPE_EXERCISE: [
            "itm_rnd"
        ],
        types.ITEM_TYPE_QUESTION: [
            "itm_standalone", "itm_rnd", "itm_difficulty"
        ]
    }[item.itm_type]
    if mcq is not None:
        cols.append("mcq_mode")
    for col in cols:
        found = False
        for row in [item, mcq]:
            try:
                val = getattr(row, col)
                found = True
            except AttributeError:
                pass
        assert found
        trs += [
            he.Tr(he.Td(he.Em(he.Txt(desc.col_desc(col))))),
            he.Tr(he.Td(www_db_util.get_attribute(ctx, col, val, item.itm_id)))
        ]

    # <tr> containing <table> with groups (if it is an mcq)
    if mcq is None:
        table_grps_id = None
        grps = None
        init_grps = None
    else:
        table_grps_id = f"table-mcq-grps-{item.itm_id}"
        grps = {
            grp.grp_id: grp.grp_name
            for grp in queries.get_submit_grps(ctx.dbs, session.usr_id(ctx))
        }
        init_grps = [
            grp.grp_id for grp in queries.get_mcq_grps(ctx.dbs, item.itm_id)
        ]
        trs += [
            he.Tr(he.Td(he.Em(he.Txt("name_groups")))),
            he.Tr(he.Td(he.Div(id_=table_grps_id)))
        ]

    # <tr> containing <table> with tags
    tags = {
        tag.tag_id: {
            "tag_id": tag.tag_id,
            "tag_name": tag.tag_name,
            "tag_color": tag.tag_color
        }
        for tag in queries.get_item_tags(ctx.dbs, item.itm_id)
    }
    trs += [
        he.Tr(he.Td(he.Em(he.Txt("name_tags")))),
        he.Tr(he.Td(he.Div(id_=table_tags_id)))
    ]

    img_instance = he.Img(
        src=base.img_src(ctx, item.itm_id, iti_num),
        alt=f"{item.itm_code}-inst-{iti_num}"
    )
    if len(all_instances) == 1:
        if all_instances[0].iti_img is not None:
            trs += [
                he.Tr(he.Td(he.Em(he.Txt("name_statement")))),
                he.Tr(he.Td(img_instance))
            ]
    else:
        options = [
            he.Option(
                he.Str(lang.txt("param_seq_instance_num") % str(i.iti_num)),
                value=i.iti_num
            ).add_flag("selected", i.iti_num == iti_num)
            for i in all_instances
        ]
        onchange = (
            f"item_admin_code_click({item.itm_id}, false, this.value);"
            " return false;"
        )
        select_instance = he.Select(
            *options,
            onchange=onchange,
            class_="select-instance"
        )
        trs += [
            he.Tr(he.Td(select_instance)),
            he.Tr(he.Td(img_instance))
        ]

    # <tr> for item content
    content = _content(ctx, item, iti_num)
    if content is not None:
        trs += [
            he.Tr(he.Td(he.Em(he.Txt("name_content")))),
            he.Tr(he.Td(content))
        ]

    # <table> containing all previous <tr>
    table_attributes = he.Table(
        *trs,
        class_="table-form"
    )

    # <div> containing item attributes and content
    div_body = he.Div(
        table_attributes,
        id_=div_body_id
    )

    # script initialising the item
    d = json.dumps
    js = (
        f"item_init_admin("
        f"{d(item.itm_id)}, {d(tags)}, {d(grps)}, {d(init_grps)})"
    )
    script = he.Script(js)

    # prepare result
    result = he.ElementList(
        div_body,
        script
    )
    return fa.responses.HTMLResponse(str(result))


def _content(
        ctx: context.Context,
        item: tables.Item,
        iti_num: int
) -> None | he.Element:
    if item.itm_type == types.ITEM_TYPE_EXERCISE:
        return _content_exercise(ctx, item)
    if item.itm_type == types.ITEM_TYPE_QUESTION:
        return _content_question(ctx, item, iti_num)
    if item.itm_type == types.ITEM_TYPE_PACK:
        return _content_pack(ctx, item)
    return he.Div()


def _content_exercise(
        ctx: context.Context,
        item: tables.Item
) -> he.Element:
    return he.ElementList(*[
        database_list.div_item(ctx, item_child, item)
        for item_child in queries.get_children(ctx.dbs, item.itm_id)
    ])


def _content_pack(
        ctx: context.Context,
        item: tables.Item
) -> he.Element:
    pack = queries.get_pack(ctx.dbs, item.itm_id)
    id_div_pack = f"div-pack-{item.itm_id}"
    div_pack = he.Div(id_=id_div_pack)
    script = he.Script(
        f"var init = {json.dumps(pack.pak_spec)};"
        f"item_pack_load({item.itm_id}, {json.dumps(id_div_pack)}, init);"
    )
    a_update = base.static_img(
        "edit",
        "verb_update",
        js=f"item_pack_update({item.itm_id});"
    )
    return he.ElementList(div_pack, a_update, script)

def _content_question(
        ctx: context.Context,
        item: tables.Item,
        iti_num: int
) -> he.Element:
    img: str | he.Element
    trs = list()
    for choice in queries.get_question_choices(ctx.dbs, item.itm_id):
        if choice.cho_correct:
            class_box = "correct"
        else:
            class_box = "wrong"
        div_status = he.Div(
            class_=f"status-box status-box-answer status-{class_box}"
        )
        img = he.Img(
            src=base.img_src(ctx, choice.cho_id, iti_num),
            alt=str(choice.cho_id)
        )
        tr = he.Tr(
            he.Td(div_status),
            he.Td(img)
        )
        trs.append(tr)
    table = he.Table(*trs)
    result = he.Div(
        table,
        class_="question-body-admin"
    )
    return result
