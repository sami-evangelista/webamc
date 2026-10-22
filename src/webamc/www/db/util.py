from webamc.www.all import *
from webamc.db import util as db_util, queries, ui, desc
from webamc.db import tables


def has_right_to_execute(
        ctx: context.Context,
        query: types.db_query_t
) -> bool:
    def get_pkey_val() -> None | tuple[types.db_col_t, types.db_base_val_t]:
        tbl = query["table"]
        pkey = db_util.get_tbl_pkey(tbl)
        pkey_name = db_util.get_col_name(pkey)
        gen = (
            (pkey, w["val"])
            for w in query.get("where", dict())
            if w["op"] == "=" and w["col"] == pkey_name
        )
        return next(gen, None)
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
        pkey_and_val = get_pkey_val()
        if (
                tbl in to_recover
                and pkey_and_val is not None
                and get_col_value(to_recover[tbl], "where") is None
        ):
            pkey, pkey_val = pkey_and_val
            row = ctx.dbs.query(
                db_util.get_tbl(tbl)
            ).where(
                db_util.get_col(pkey) == pkey_val
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
            "question": "qst_id",
            "item_relation": "itr_child"
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
        col: types.db_col_t,
        val: types.db_base_val_t,
        id_: int,
        updatable: bool = True
) -> he.Element:
    tbl = db_util.get_col_tbl(col)
    col_name = db_util.get_col_name(col)
    tbl_name = db_util.get_tbl_name(tbl)
    pkey = db_util.get_tbl_pkey(tbl)
    pkey_name = db_util.get_col_name(pkey)
    updatable = updatable and db_util.is_col_updatable(col)
    if updatable:
        where: types.db_where_t = {
            "op": "=",
            "col": pkey.name,
            "val": id_
        }
        query: types.db_query_t = {
            "type": "update",
            "table": tbl_name,
            "where": [where]
        }
        updatable = has_right_to_execute(ctx, query)

    val_escape_html, val = val_fmt(ctx, col, val)
    element_val = he.Str(val, escape=val_escape_html)
    if not updatable:
        return element_val

    div_id = f"div-{col_name}-{id_}"
    js = f"db_col_show_input({id_}, '{col_name}', '{pkey_name}')"
    a_id = f"{div_id}-link"
    a = he.A(
        he.Div(element_val, id_=f"{div_id}-val"),
        href=f"javascript:{js}",
        id_=a_id
    )
    div_input = he.Div(
        he.Empty(),
        style="display: none;",
        id_=f"{div_id}-input"
    )
    result = he.Div(a, div_input)
    return result


def html_element(
        ctx: context.Context,
        col: types.db_col_t,
        prefix: str = "col-",
        val: None | types.db_base_val_t = None
) -> he.Element:
    col_name = db_util.get_col_name(col)
    input_type = get_col_input_type(ctx, col)
    input_id = prefix + col_name
    return input_type.element(value=val, name=input_id, id=input_id)


def get_filter_wheres(
        tbl: sa.Table | str,
        args: dict[str, tp.Any]
) -> list[sa.sql.elements.BinaryExpression[tp.Any]]:
    result: list[sa.sql.elements.BinaryExpression[tp.Any]] = list()
    typed_value: tp.Any
    for col in db_util.get_tbl_visible_cols(tbl):
        col_name = db_util.get_col_name(col)
        value = args.get(col_name)
        oper = args.get(col_name + "-cmp")
        if value is not None and oper is not None:
            # this should not be necessary to type the value
            # because values received should be correct
            if value is None:
                typed_value = None
            elif isinstance(db_util.get_col_type(col), sa.Integer):
                typed_value = int(value)
            elif isinstance(db_util.get_col_type(col), sa.Boolean):
                typed_value = bool(value)
            else:
                typed_value = str(value)
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


def get_col_input_type(
        ctx: context.Context,
        col: types.db_col_t
) -> ui.Input:
    c = db_util.get_col(col)
    return db_util.get_col_type(c).get_input(c, dbs=ctx.dbs)


def val_fmt(
        ctx: context.Context,
        col: types.db_col_t,
        val: types.db_base_val_t
) -> tuple[bool, str]:
    c = db_util.get_col(col)
    return db_util.get_col_type(c).val_fmt(val, dbs=ctx.dbs)


def get_txt_and_input(
        ctx: context.Context,
        *col: types.db_col_t
) -> tp.Iterable[tuple[he.Element, he.Element]]:
    for c in col:
        label = base.field_label(desc.col_txt(c))
        inpt = get_col_input_type(ctx, c).element()
        yield (label, inpt)


def get_attributes(
        ctx: context.Context,
        get_val: tp.Callable[[types.db_col_t], types.db_base_val_t],
        *col: types.db_col_t,
        updatable: bool = True
) -> tp.Generator[tuple[he.Element, he.Element]]:
    pkey: None | types.db_col_t = None
    val: int
    for c in col:
        if pkey is None:
            pkey = db_util.get_tbl_pkey(db_util.get_col_tbl(c))
            val = tp.cast(int, get_val(pkey.name))
        a = get_attribute(ctx, c, get_val(c), val, updatable=updatable)
        l = base.field_label(desc.col_txt(c))
        yield (l, a)
