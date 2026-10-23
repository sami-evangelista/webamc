import typing as tp
import typing_extensions as tp_ext


question_type_t = tp.Literal[0, 1]
QUESTION_TYPE_SINGLE: question_type_t = 0
QUESTION_TYPE_MULTI: question_type_t = 1

mcq_mode_t = tp.Literal[0, 1]
MCQ_MODE_EXAM: mcq_mode_t = 0
MCQ_MODE_REVIEW: mcq_mode_t = 1

item_type_t = tp.Literal[0, 1, 2, 3]
ITEM_TYPE_CHOICE: item_type_t = 0
ITEM_TYPE_EXERCISE: item_type_t = 1
ITEM_TYPE_PACK: item_type_t = 2
ITEM_TYPE_QUESTION: item_type_t = 3

item_difficulty_t = tp.Literal[1, 2, 3, 4, 5]
ITEM_MIN_DIFFICULTY: item_difficulty_t = 1
ITEM_MAX_DIFFICULTY: item_difficulty_t = 5

usr_right_t = tp.Literal[1, 2]
USR_RIGHT_VIEW: usr_right_t = 1
USR_RIGHT_SUBMIT: usr_right_t = 2

ticket_type_t = tp.Literal[0, 1, 2]
TICKET_PASSWORD_CHANGE: ticket_type_t = 0
TICKET_EADDR_CHANGE: ticket_type_t = 1
TICKET_ACCOUNT_CREATION: ticket_type_t = 2

submission_type_t = tp.Literal[0, 1]
SUBMISSION_TYPE_EXAM: submission_type_t = 0
SUBMISSION_TYPE_REVIEW: ticket_type_t = 1

pack_op_t = tp.Literal[
    "all",
    "by-difficulty",
    "by-tag",
    "head",
    "shuf",
    "sort"
]

dict_pack_spec_t = tp_ext.TypedDict(
    "dict_pack_spec_t",
    {
        "op": pack_op_t,
        "arg": tp.Any,
        "rev": bool,
        "content": "pack_spec_t"
    },
    total=False
)

pack_spec_t = tp.Union[list["dict_pack_spec_t"], dict_pack_spec_t]

item_mdata_t = tp.Literal[
    "CODE",
    "DIFFICULTY",
    "INSTANCES",
    "RND",
    "STANDALONE",
    "TAG",
    "TITLE",
    "VISIBLE"
]

mcq_content_t = tp_ext.TypedDict(
    "mcq_content_t",
    {
        "itm_id": int,
        "itm_type": item_type_t,
        "itm_qst_type": question_type_t,
        "iti_id": int,
        "iti_num": int,
        "children": None | list["mcq_content_t"]
    }
)


def mcq_enum_items(
        content: mcq_content_t,
        parent: mcq_content_t | None = None
) -> tp.Generator[tuple[mcq_content_t, None | mcq_content_t]]:
    yield content, parent
    if content["children"] is not None:
        for c in content["children"]:
            yield from mcq_enum_items(c, content)
