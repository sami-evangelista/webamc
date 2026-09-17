from webamc.www.all import *
from webamc.db import tables, desc, queries
from webamc.www.db import util as www_db_util
from . import database_list


def page(
        ctx: context.Context,
        itm_id: int,
        iti_num: int = 1
) -> fa.Response:

    owner = queries.get_item_owner(ctx.dbs, itm_id)
    if owner is None or owner.usr_id != session.usr_id(ctx):
        raise fa.HTTPException(status_code=403)

    item = queries.get_item(ctx.dbs, itm_id)
    mcq = queries.get_item_mcq(ctx.dbs, item.itm_id)

    # all instances of a question
    all_instances = queries.get_instances(ctx.dbs, item.itm_id)

    table_tags_id = f"table-item-tags-{item.itm_id}"
    div_body_id = f"div-item-body-{item.itm_id}"

    # <tr> containing attributes
    trs: list[he.Tr] = list()
    if session.has_admin_right(ctx, item):
        a_delete = base.static_img(
            "trash",
            "verb_delete",
            js=f"item_delete({item.itm_id});"
        )
        if item.itm_type == types.ITEM_TYPE_QUESTION:
            a_delete_instance = he.Button(
                he.Txt("action_delete_instance"),
                onclick=
                f"if(confirm('{lang.txt('msg_confirm_delete_instance')}'))" + \
                f"{{ item_instance_delete({item.itm_id}, {iti_num}); }}",
                class_="btn-small btn-danger"
            )
            tr = he.Tr(
                he.Td(),
                he.Td(
                    a_delete,
                    he.Str(" "),
                    a_delete_instance
                ),
            )
        else:
            tr = he.Tr(
                he.Td(),
                he.Td(a_delete)
            )

        trs.append(tr)

    if all_instances:
        options = []
        for inst in all_instances:
            # On génère le texte traduit une seule fois pour éviter de se répéter
            inst_text = f"{lang.txt('name_instance')} {inst.iti_num}"

            if int(inst.iti_num) == int(iti_num):
                options.append(
                    he.Option(
                        he.Str(inst_text),
                        value=inst.iti_num,
                        selected="selected"
                    )
                )
            else:
                options.append(
                    he.Option(
                        he.Str(inst_text),
                        value=inst.iti_num
                    )
                )

        selector = he.Select(
            *options,
            onchange=f"item_admin_code_click({item.itm_id}, this.value);"+ \
            " return false;",
            class_="select-instance"
        )
        trs.append(
            he.Tr(
                he.Td(
                    he.Txt("name_instance")
                ),
                he.Td(selector)
            )
        )

    # select item columns to show
    cols = ["itm_title", "itm_date"]
    cols += {
        types.ITEM_TYPE_PACK: [
        ],
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
        tr = he.Tr(
            he.Td(he.Txt(desc.col_desc(col))),
            he.Td(
                www_db_util.get_attribute(ctx, col, val, item.itm_id)
            )
        )
        trs.append(tr)

    if all_instances:
        img = he.Img(
            src=base.img_src(
                ctx,
                item.itm_id,
                iti_num,
            ),
            alt=f"{item.itm_code}-inst-{iti_num}"
        )
        tr=he.Tr(
            he.Td(
                he.Txt("name_statement")
            ),
            he.Td(img)
        )
        trs.append(tr)

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
        tr = he.Tr(
            he.Td(he.Txt("name_groups")),
            he.Td(he.Div(id_=table_grps_id))
        )
        trs.append(tr)

    # <tr> containing <table> with tags
    tags = {
        tag.tag_id: {
            "tag_id": tag.tag_id,
            "tag_name": tag.tag_name,
            "tag_color": tag.tag_color
        }
        for tag in queries.get_item_tags(ctx.dbs, item.itm_id)
    }
    tr = he.Tr(
        he.Td(he.Txt("name_tags")),
        he.Td(he.Div(id_=table_tags_id))
    )
    trs.append(tr)

    # <tr> containing item image

    # <tr> for item content
    content = _content(ctx, item, iti_num)
    if content is not None:
        tr = he.Tr(
            he.Td(),
            he.Td(content)
        )
        trs.append(tr)

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
        f"item_new_item_admin("
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
        iti_num: int=1
) -> None | he.Element:
    try:
        if item.itm_type == types.ITEM_TYPE_EXERCISE:
            return _content_exercise(ctx, item)
        if item.itm_type == types.ITEM_TYPE_QUESTION:
            return _content_question(ctx, item, iti_num)
    except KeyError:
        return None
    return he.Div()


def _content_exercise(
        ctx: context.Context,
        item: tables.Item
) -> he.Element:
    return he.ElementList(*[
        database_list.div_item(ctx, row)
        for row in queries.get_children(ctx.dbs, item.itm_id)
    ])


def _content_question(
        ctx: context.Context,
        item: tables.Item,
        iti_num: int = 1
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
