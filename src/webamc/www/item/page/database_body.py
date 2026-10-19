from sqlalchemy.orm.attributes import InstrumentedAttribute

from webamc.www.all import *
from webamc.db import tables, queries, util as db_util
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
    all_instances = queries.get_instances(ctx.dbs, item.itm_id)

    table_tags_id = f"table-item-tags-{item.itm_id}"

    # <tr> containing attributes
    trs: list[he.Element] = list()

    # select item columns to show
    cols: list[InstrumentedAttribute[tp.Any]] = [
        tables.Item.itm_code,
        tables.Item.itm_title,
        tables.Item.itm_date,
        tables.Item.itm_visible
    ]
    if item.itm_is_mcq:
        cols.append(tables.Item.itm_mcq_mode)
    if item.itm_type in {types.ITEM_TYPE_EXERCISE, types.ITEM_TYPE_QUESTION}:
        cols.append(tables.Item.itm_rnd)
    if item.itm_type == types.ITEM_TYPE_QUESTION:
        cols.append(tables.Item.itm_difficulty)
        cols.append(tables.Item.itm_qst_type)
        cols.append(tables.Item.itm_qst_standalone)
    def get_val(col: types.db_col_t) -> types.db_base_val_t:
        return getattr(item, db_util.get_col_name(col))  # type: ignore
    for label, inpt in www_db_util.get_attributes(ctx, get_val, *cols):
        trs.append(label)
        trs.append(inpt)

    # <tr> containing <table> with groups (if it is an mcq)
    if not item.itm_is_mcq:
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
            base.field_label(he.Txt("word_groups")),
            he.Div(id_=table_grps_id)
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
        base.field_label(he.Txt("word_tags")),
        he.Div(id_=table_tags_id)
    ]

    img_instance = he.Img(
        src=base.img_src(ctx, item.itm_id, iti_num),
        alt=f"{item.itm_code}-inst-{iti_num}"
    )
    if len(all_instances) == 1:
        if all_instances[0].iti_img is not None:
            trs += [
                base.field_label(he.Txt("word_statement")),
                img_instance
            ]
    else:
        options = [
            he.Option(
                he.Str(lang.txt("param_seq_instance_num", str(i.iti_num))),
                value=i.iti_num
            ).add_flag("selected", i.iti_num == iti_num)
            for i in all_instances
        ]
        onchange = (
            f"item_db_code_click({item.itm_id}, false, this.value);"
            " return false;"
        )
        select_instance = he.Select(
            *options,
            onchange=onchange,
            class_="select-instance"
        )
        trs += [select_instance, img_instance]

    # <tr> with select containing elements that can be added to the
    # exercise
    children: None | list[tables.Item] = None
    select_add: None | he.Element = None
    if item.itm_type == types.ITEM_TYPE_EXERCISE:
        def option_str(item: tables.Item) -> str:
            assert item.itm_code is not None
            if item.itm_type == types.ITEM_TYPE_QUESTION:
                return (
                    lang.txt("word_question").title()
                    + " [" + item.itm_code + "]"
                )
            if item.itm_type == types.ITEM_TYPE_EXERCISE:
                return (
                    lang.txt("word_exercise").title()
                    + " [" + item.itm_code + "]"
                )
            assert False
        options = [he.Option(he.Txt("seq_add_an_item"), value="")]
        children = queries.get_children(ctx.dbs, item.itm_id)
        if not item.itm_is_mcq:
            ok_types = {types.ITEM_TYPE_QUESTION}
        else:
            if children == list():
                ok_types = {types.ITEM_TYPE_EXERCISE, types.ITEM_TYPE_QUESTION}
            else:
                ok_types = {children[0].itm_type}
        excluded_items = set(c.itm_id for c in children)
        candidate_items = sorted(
            (option_str(item), item.itm_id)
            for item in queries.get_usr_items(ctx.dbs, session.usr_id(ctx))
            if item.itm_type in ok_types
            and not item.itm_is_mcq
            and item.itm_id not in excluded_items
        )
        if candidate_items != list():
            options += [
                he.Option(he.Str(opt), value=str(val))
                for (opt, val) in candidate_items
            ]
            select_add = he.Select(
                *options,
                id_=f"select-add-child-{item.itm_id}",
                onchange=f"item_db_add_child({item.itm_id})"
            ).set_data("type", "integer")

    # <tr> for item content
    content = _content(ctx, item, iti_num, children)
    if content is not None or select_add is not None:
        trs.append(base.field_label(he.Txt("word_content")))
        if select_add is not None:
            trs.append(select_add)
        if content is not None:
            trs.append(content)

    # <table> containing all previous <tr>
    table_attributes = he.mktable(((tr, ) for tr in trs), class_="table-form")

    # script initialising the item
    d = json.dumps
    js = (
        f"item_db_init("
        f"{d(item.itm_id)}, {d(tags)}, {d(grps)}, {d(init_grps)})"
    )
    script = he.Script(js)

    result = he.ElementList(
        table_attributes,
        script
    )
    return fa.responses.HTMLResponse(str(result))


def _content(
        ctx: context.Context,
        item: tables.Item,
        iti_num: int,
        children: list[tables.Item] | None
) -> None | he.Element:
    if item.itm_type == types.ITEM_TYPE_EXERCISE:
        return _content_exercise(ctx, item, children)
    if item.itm_type == types.ITEM_TYPE_QUESTION:
        return _content_question(ctx, item, iti_num, children)
    if item.itm_type == types.ITEM_TYPE_PACK:
        return _content_pack(ctx, item)
    return he.Empty()


def _content_exercise(
        ctx: context.Context,
        item: tables.Item,
        children: list[tables.Item] | None
) -> None | he.Element:
    if children is None:
        children = queries.get_children(ctx.dbs, item.itm_id)
    if children == list():
        return None
    return he.ElementList(*[
        database_list.div_item(ctx, item_child, item)
        for item_child in children
    ])


def _content_pack(
        ctx: context.Context,
        item: tables.Item
) -> he.Element:
    id_div_pack = f"div-pack-{item.itm_id}"
    div_pack = he.Div(id_=id_div_pack)
    script = he.Script(
        f"var init = {json.dumps(item.itm_pack_spec)};"
        f"item_db_pack_load({item.itm_id}, {json.dumps(id_div_pack)}, init);"
    )
    a_update = base.static_img(
        "edit",
        "word_update",
        js=f"item_db_pack_update({item.itm_id});"
    )
    content = he.ElementList(div_pack, a_update, script)
    return content


def _content_question(
        ctx: context.Context,
        item: tables.Item,
        iti_num: int,
        children: list[tables.Item] | None
) -> he.Element:
    img: str | he.Element
    trs = list()
    if children is None:
        children = queries.get_children(
            ctx.dbs,
            item.itm_id,
            types.ITEM_TYPE_CHOICE
        )
    for cho in children:
        if cho.itm_cho_correct:
            class_box = "correct"
        else:
            class_box = "wrong"
        div_status = he.Div(
            class_=f"status-box status-box-answer status-{class_box}"
        )
        img = he.Img(
            src=base.img_src(ctx, cho.itm_id, iti_num),
            alt=str(cho.itm_id)
        )
        trs.append([div_status, img])
    div_choices = he.Div(
        he.mktable(trs),
        class_="question-body-admin"
    )
    return div_choices
