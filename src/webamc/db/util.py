from sqlalchemy import Column, Table
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.orm.attributes import InstrumentedAttribute

from webamc.all import *
from . import tables


def get_tbl(t: types.db_tbl_t) -> Table:
    if isinstance(t, Table):
        return t
    if isinstance(t, str):
        return struct["tbls"][t]["def"]
    return t.__table__  # type: ignore


def get_tbl_name(t: types.db_tbl_t) -> str:
    return get_tbl(t).name


def get_tbl_meta(t: types.db_tbl_t) -> DeclarativeMeta:
    if isinstance(t, str):
        return struct["tbls"][t]["meta"]
    if isinstance(t, Table):
        return get_tbl_meta(get_tbl_name(t))
    return t


def get_tbl_pkey(t: types.db_tbl_t) -> Column[tp.Any]:
    return struct["tbls"][get_tbl_name(t)]["pkey"]


def get_tbl_fkeys(
        t: types.db_tbl_t
) -> dict[Column[tp.Any], list[Column[tp.Any]]]:
    return struct["tbls"][get_tbl_name(t)]["fkeys"]


def get_tbl_cols(t: types.db_tbl_t) -> list[Column[tp.Any]]:
    return struct["tbls"][get_tbl_name(t)]["cols"]


def get_info(t: types.db_tbl_t, f: str) -> tp.Any | None:
    info = getattr(get_tbl_meta(t), "info", None)
    if info is None:
        return None
    return info.get(f, None)


def get_tbl_doc(t: types.db_tbl_t) -> str | None:
    return get_info(t, "doc")


def get_tbl_code(t: types.db_tbl_t) -> Column[tp.Any] | None:
    c = get_info(t, "code")
    if c is None:
        return None
    return get_col(c)


def get_col(c: types.db_col_t) -> Column[tp.Any]:
    if isinstance(c, str):
        return struct["cols"][c]["def"]
    if isinstance(c, InstrumentedAttribute):
        return get_col(c.name)
    return c


def get_col_name(c: types.db_col_t) -> str:
    if isinstance(c, str):
        return c
    return c.name


def get_col_doc(c: types.db_col_t) -> str | None:
    return get_col(c).info.get("doc")


def get_col_tbl(c: types.db_col_t) -> Table:
    return struct["cols"][get_col_name(c)]["tbl"]


def get_all_tbl_names() -> tp.Generator[str]:
    yield from struct["tbls"]


def is_col_visible(c: types.db_col_t) -> bool:
    return bool(get_col(c).info.get("ui_visible", False))


def is_col_updatable(c: types.db_col_t) -> bool:
    return bool(get_col(c).info.get("ui_updatable", False))


def get_tbl_visible_cols(t: types.db_tbl_t) -> tp.Generator[Column[tp.Any]]:
    for c in get_tbl_cols(t):
        if is_col_visible(c):
            yield c


def get_tbl_updatable_cols(t: types.db_tbl_t) -> tp.Generator[Column[tp.Any]]:
    for c in get_tbl_cols(t):
        if is_col_updatable(c):
            yield c


db_struct_tbl_t = tp.TypedDict(
    "db_struct_tbl_t",
    {
        "meta": DeclarativeMeta,
        "def": Table,
        "cols": list[Column[tp.Any]],
        "pkey": Column[tp.Any],
        "fkeys": dict[Column[tp.Any], list[Column[tp.Any]]]
    },
    total=True
)
db_struct_col_t = tp.TypedDict(
    "db_struct_col_t",
    {
        "def": Column[tp.Any],
        "tbl": Table
    },
    total=True
)
db_struct_t = tp.TypedDict(
    "db_struct_t",
    {
        "tbls": dict[str, db_struct_tbl_t],
        "cols": dict[str, db_struct_col_t]
    }
)


struct: db_struct_t


def _init(base: tp.Any) -> None:
    global struct
    struct = {
        "tbls": dict(),
        "cols": dict()
    }
    todo = list(base.__subclasses__())
    done: set[tp.Type[base]] = set()
    while todo != list():
        tbl_cls = todo.pop()
        tbl = tbl_cls.__table__
        struct["tbls"][tbl.name] = {
            "meta": tbl_cls,
            "def": tbl,
            "cols": list(tbl.columns),
            "pkey": next(col for col in tbl.columns if col.primary_key),
            "fkeys": {
                col: [fkey.column for fkey in col.foreign_keys]
                for col in tbl.columns
                if len(col.foreign_keys) > 0
            }
        }
        for col in tbl.columns:
            struct["cols"][col.name] = {
                "def": col,
                "tbl": tbl
            }
        done.add(tbl_cls)
        todo += tbl_cls.__subclasses__()

    # perform some checks

    # only one column forms the primary key
    for tbl, tbl_def in struct["tbls"].items():
        assert 1 == len(
            [col for col in tbl_def["def"].columns if col.primary_key]
        )

    # a foreign or a primary key can only be an integer
    for tbl, tbl_def in struct["tbls"].items():
        assert isinstance(tbl_def["pkey"].type, sa.Integer)
        for fkey in tbl_def["fkeys"]:
            assert isinstance(fkey.type, sa.Integer)

    # a code column can only be an integer or a string
    for tbl, tbl_def in struct["tbls"].items():
        col = get_tbl_code(tbl)
        if col is not None:
            assert isinstance(col.type, (sa.String, sa.Integer))


_init(tables.Base)
