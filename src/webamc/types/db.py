import datetime
import typing as tp
import typing_extensions as tp_ext


db_base_val_t = str | int | bool | datetime.date | datetime.datetime | None

db_map_t = dict[str, db_base_val_t]

db_query_result_t = tp_ext.TypedDict(
    "db_query_result_t",
    {
        "values": list[list[db_map_t]] | list[db_map_t],
        "readable_values": list[list[db_map_t]] | list[db_map_t]
    },
    total=False
)

db_where_t = tp_ext.TypedDict(
    "db_where_t",
    {
        "col": str,
        "op": tp.Literal["=", "like"],
        "val": db_base_val_t
    }
)

db_query_type_t = tp.Literal[
    "delete",
    "insert",
    "select",
    "update"
]

db_query_t = tp_ext.TypedDict(
    "db_query_t",
    {
        "type": db_query_type_t,
        "table": str,
        "values": db_map_t,
        "where": list[db_where_t]
    },
    total=False
)
