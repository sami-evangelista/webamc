import typing as tp
import typing_extensions as tp_ext


load_single_result_t = tp_ext.TypedDict(
    "load_single_result_t",
    {
        "status": tp.Literal[0, 1, 2],
        "msg": str
    }
)

load_result_t = list[load_single_result_t]


def literal_type_values(t: tp._SpecialForm) -> set[tp.Any]:
    return set(tp.get_args(t))
