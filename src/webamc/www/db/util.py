from webamc.www.all import *
from webamc.db import util as db_util, queries, ui, col_types as ct, desc
from webamc.db import tables


def has_right_to_execute(
        ctx: context.Context,
        query: types.db_query_t
) -> bool:
    def get_col_value(
            col_name: str,
            clause: tp.Literal["where", "values"]
    ) -> types.db_base_val_t:
        if clause == "where":
            return next(
                (
                    w["val"]
                    for w in query["where"]
                    if w["col"] == col_name and w["op"] == "="
                ),
                None
            )
        try:
            return query["values"][col_name]
        except KeyError:
            return None
    def check_item_id(itm_id: types.db_base_val_t) -> bool:
        if itm_id is None or not isinstance(itm_id, int):
            return False
        owner = queries.get_item_owner(ctx.dbs, itm_id)
        return owner is not None and owner.usr_id == session.usr_id(ctx)
    def recover_values() -> None:
        # for some tables we need to recover a column value if not
        # present
        to_recover = {
            "exam": "exm_mcq"
        }
        pkey_and_val = get_pkey_val(query)
        if (
                tbl in to_recover
                and pkey_and_val is not None
                and get_col_value(to_recover[tbl], "where") is None
        ):
            pkey, pkey_val = pkey_and_val
            row = ctx.dbs.query(
                db_util.get_tbl(tbl)
            ).where(
                pkey == pkey_val
            ).first()
            if row is not None:
                w: types.db_where_t = {
                    "op": "=",
                    "val": getattr(row, to_recover[tbl]),
                    "col": to_recover[tbl]
                }
                query["where"].append(w)

    tbl = query["table"]
    typ = query["type"]

    # a user allowed to administrate tbl can execute anything on it
    if session.can_admin_table(ctx, tbl):
        return True

    # select queries on table tag can be performed by anyone
    if (tbl, typ) == ("tag", "select"):
        return True

    # for a deletion in table registration we need to get the mcq
    # creator
    if (tbl, typ) == ("registration", "delete"):
        reg_id = get_col_value("reg_id", "where")
        if reg_id is None:
            return False
        item = ctx.dbs.query(
            tables.Item
        ).where(
            (tables.Registration.reg_id == reg_id)
            & (tables.Registration.reg_exam == tables.Exam.exm_id)
            & (tables.Item.itm_id == tables.Exam.exm_mcq)
        ).first()
        if item is None:
            return False
        return item.itm_usr == session.usr_id(ctx)

    # any query referencing an item owned by the user is ok
    try:
        recover_values()
        col_item = {
            "answer": "ans_id",
            "exam": "exm_mcq",
            "exercise": "exe_id",
            "item": "itm_id",
            "item_tag": "itg_item",
            "mcq": "mcq_id",
            "mcq_grp": "mgp_mcq",
            "pack": "pak_id",
            "question": "qst_id"
        }[tbl]
        if typ in {"delete", "select", "update"}:
            return check_item_id(get_col_value(col_item, "where"))
        return check_item_id(get_col_value(col_item, "values"))
    except KeyError:
        pass

    # all other queries are forbidden
    return False


def get_attribute(
        ctx: context.Context,
        col: str | sa.Column[tp.Any],
        val: types.db_base_val_t,
        id_: int,
        values: None | types.db_map_t = None,
        updatable: bool = True
) -> he.Element:
    if isinstance(col, str):
        col = db_util.get_col(col)
    tbl = db_util.get_col_tbl(col)
    tbl_name = db_util.get_tbl_name(tbl)
    pkey = db_util.get_tbl_pkey(tbl)
    updatable = updatable and is_updatable(col)
    input_type = get_col_input_type(ctx, col)
    if updatable:
        where: list[types.db_where_t] = list()
        if values is not None:
            where += [
                {"op": "=", "col": col_name, "val": val}
                for col_name, val in values.items()
            ]
        where.append({"op": "=", "col": pkey.name, "val": id_})
        query: types.db_query_t = {
            "type": "update",
            "table": tbl_name,
            "where": where
        }
        updatable = has_right_to_execute(ctx, query)

    if input_type.direct_update():
        elements = html_element(
            ctx,
            col,
            prefix=f"col_{id_}-",
            val=val,
            id_=id_,
            updatable=updatable
        )
        return he.ElementList(*elements)

    val = format_value(ctx, col, val)
    if not updatable:
        return he.Str(val)

    div_id = f"div-{col.name}-{id_}"
    js = f"db_col_show_input('{id_}', '{col.name}', '{pkey.name}')"
    a_id = f"{div_id}-link"
    span_val_id = f"{div_id}-val"
    a = he.A(
        he.Span(he.Str(val), id_=span_val_id),
        href=f"javascript:{js}",
        id_=a_id
    )
    span_input_id = f"{div_id}-input"
    span_input = he.Span(
        he.Empty(),
        style="display: none;",
        id_=span_input_id
    )
    result = he.Div(a, span_input)
    return result


def html_element(
        ctx: context.Context,
        col: sa.Column[tp.Any],
        prefix: str = "col-",
        val: None | types.db_base_val_t = None,
        id_: None | int = None,
        updatable: bool = True
) -> list[he.Element]:

    # get DB table and column informations
    col_name = db_util.get_col_name(col)
    tbl = db_util.get_col_tbl(col)
    tbl_name = db_util.get_tbl_name(tbl)
    pkey = db_util.get_tbl_pkey(tbl)

    # get UI information
    updatable = updatable and is_updatable(col)
    input_type = get_col_input_type(ctx, col)

    input_id = prefix + col_name
    input_field = input_type.element()
    input_field["name"] = input_id
    input_field["id"] = input_id

    # set db_args for the javascript initialisation function
    if id_ is None:
        db_args = None
    else:
        db_args = {
            "tbl_name": tbl_name,
            "pkey_name": pkey.name,
            "id": id_,
            "col_name": col.name
        }

    # call the javascript initialisation function or simply set the
    # value of the input field if the type does not have one
    d = json.dumps
    if input_type.js_init_fun == "":
        js = f"$('#{input_id}').val({d(val, default=str)});"
    else:
        js = f"{input_type.js_init_fun}({d(input_id)}, {d(val)}"
        js += f", {d(not updatable)}, {d(db_args)});"

    return [input_field, he.Script(js)]


def get_filter_wheres(
        tbl: sa.Table | str,
        args: dict[str, tp.Any]
) -> list[sa.sql.elements.BinaryExpression[tp.Any]]:
    cols = [col for col in db_util.get_tbl_cols(tbl) if is_visible(col)]
    result: list[sa.sql.elements.BinaryExpression[tp.Any]] = list()
    for col in cols:
        col_name = db_util.get_col_name(col)
        op_name = col_name + "-cmp"
        if col_name in args:
            value = args[col_name]
            typed_value: tp.Any
            if isinstance(col.type, sa.Integer):
                typed_value = int(value)
            elif isinstance(col.type, sa.Boolean):
                typed_value = bool(value)
            else:
                typed_value = str(value)
            oper = args.get(op_name)
            if oper == "=":
                result.append(col == typed_value)
            elif oper == "!=":
                result.append(col != typed_value)
            elif oper == "<":
                result.append(col < typed_value)
            elif oper == ">":
                result.append(col > typed_value)
            elif oper == "like":
                result.append(col.like(f"%{typed_value}%"))
            elif oper == "notlike":
                result.append(col.notlike(f"%{typed_value}%"))
    return result


def get_pkey_val(
        query: types.db_query_t
) -> None | tuple[sa.Column[tp.Any], types.db_base_val_t]:
    tbl = query["table"]
    pkey = db_util.get_tbl_pkey(tbl)
    pkey_name = db_util.get_col_name(pkey)
    gen = (
        (pkey, w["val"])
        for w in query.get("where", dict())
        if w["op"] == "=" and w["col"] == pkey_name
    )
    return next(gen, None)


def is_visible(col: str | sa.Column[tp.Any]) -> bool:
    if isinstance(col, str):
        col = db_util.get_col(col)
    col_name = db_util.get_col_name(col)
    return col_name in cols_visible


def is_updatable(col: str | sa.Column[tp.Any]) -> bool:

    # get informations on the column's table
    if isinstance(col, str):
        col = db_util.get_col(col)
    col_name = db_util.get_col_name(col)
    tbl = db_util.get_col_tbl(col)
    pkey = db_util.get_tbl_pkey(tbl)

    return col is not pkey and col_name in cols_updatable


def get_col_input_type(
        ctx: context.Context,
        col: str | sa.Column[tp.Any]
) -> ui.Input:
    if isinstance(col, str):
        col = db_util.get_col(col)
    return tp.cast(ct.ColType, col.type).get_input(col, dbs=ctx.dbs)


def format_value(
        ctx: context.Context,
        col: sa.Column[tp.Any],
        val: types.db_base_val_t
) -> str:
    return tp.cast(ct.ColType, col.type).val_fmt(val, dbs=ctx.dbs)


def get_txt_and_input(
        ctx: context.Context,
        cols: list[str]
) -> tp.Iterable[tuple[he.Element, he.Element]]:
    for col_name in cols:
        col = db_util.get_col(col_name)
        yield (desc.col_txt(col_name), get_col_input_type(ctx, col).element())


def get_attributes(
        ctx: context.Context,
        cols: list[str],
        get_val: tp.Callable[[str], types.db_base_val_t],
        updatable: bool = True
) -> tp.Iterable[tuple[he.Element, he.Element]]:
    if cols != list():
        pkey = db_util.get_tbl_pkey(db_util.get_col_tbl(cols[0]))
        pkey_val = tp.cast(int, get_val(pkey.name))
        yield from (
            (
                desc.col_txt(col),
                get_attribute(
                    ctx, col, get_val(col), pkey_val, updatable=updatable
                )
            )
            for col in cols
        )


# columns that are visible from the web interface
cols_visible = {
    "atr_id",
    "atr_code",
    "atr_desc",
    "adm_id",
    "adm_tbl",
    "adm_usr",
    "loc_enabled",
    "loc_id",
    "loc_login",
    "loc_usr",
    "cas_enabled",
    "cas_id",
    "cas_login",
    "cas_usr",
    "exm_duration",
    "exm_id",
    "exm_mcq",
    "exm_start",
    "grp_id",
    "grp_name",
    "grp_parent",
    "itm_code",
    "itm_difficulty",
    "itm_rnd",
    "itm_standalone",
    "mcq_mode",
    "tag_color",
    "tag_desc",
    "tag_name",
    "tbl_name",
    "uat_usr",
    "uat_attr",
    "uat_value",
    "ugp_grp",
    "ugp_id",
    "ugp_right",
    "ugp_usr",
    "usr_code",
    "usr_eaddr",
    "usr_fst_name",
    "usr_id",
    "usr_name",
    "rvs_usr",
    "rvs_mcq"
}


# columns that can be updated from the web interface
cols_updatable = {
    "atr_code",
    "atr_desc",
    "adm_tbl",
    "adm_usr",
    "loc_enabled",
    "loc_login",
    "loc_usr",
    "cas_enabled",
    "cas_login",
    "cas_usr",
    "exm_duration",
    "exm_mcq",
    "exm_start",
    "grp_name",
    "grp_parent",
    "itm_difficulty",
    "itm_rnd",
    "itm_title",
    "itm_standalone",
    "mcq_mode",
    "tag_color",
    "tag_desc",
    "tag_name",
    "tbl_name",
    "uat_usr",
    "uat_attr",
    "uat_value",
    "ugp_grp",
    "ugp_right",
    "ugp_usr",
    "usr_code",
    "usr_eaddr",
    "usr_fst_name",
    "usr_name"
}
