import datetime
import typing as tp
import typing_extensions as tp_ext
import sqlalchemy as sa
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.decl_api import DeclarativeMeta


db_col_t = str | sa.Column[tp.Any] | InstrumentedAttribute[tp.Any]

db_tbl_t = str | sa.Table | DeclarativeMeta

db_base_val_t = (
    str | int | bool | float | datetime.date | datetime.datetime | None
)

db_map_t = dict[str, db_base_val_t]

class db_where_t(tp_ext.TypedDict):
    col: str
    op: tp.Literal["=", "like"]
    val: db_base_val_t

db_query_type_t = tp.Literal[
    "delete",
    "insert",
    "select",
    "update"
]

class db_query_t(tp_ext.TypedDict):
    type: db_query_type_t
    table: str
    values: tp.NotRequired[db_map_t]
    where: tp.NotRequired[list[db_where_t]]
