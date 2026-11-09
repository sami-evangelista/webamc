import json
import typing as tp
import typing_extensions as tp_ext
from pydantic import TypeAdapter, ValidationError


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

message_type_t = tp.Literal[0, 1]
MESSAGE_TYPE_FILE: message_type_t = 0
MESSAGE_TYPE_SUBMISSION: message_type_t = 1

pack_op_t = tp.Literal[
    "all",
    "by-tag",
    "head",
    "shuf"
]

item_mdata_t = tp.Literal[
    "CODE",
    "INSTANCES",
    "RND",
    "STANDALONE",
    "TAG",
    "TITLE",
    "VISIBLE"
]

exam_status_t = tp.Literal[
    "finished",
    "in-progress",
    "upcoming"
]

exam_usr_status_t = tp.Literal[
    "absent",
    "inactive",
    "not-started",
    "online",
    "finished"
]

class mcq_content_t(tp_ext.TypedDict):
    itm_id: int
    itm_type: item_type_t
    itm_qst_type: question_type_t
    iti_id: int
    iti_num: int
    children: None | list["mcq_content_t"]

class dict_pack_spec_t(tp.TypedDict):
    op: tp.NotRequired[pack_op_t]
    arg: tp.NotRequired[tp.Any]
    rev: tp.NotRequired[bool]
    content: tp.NotRequired[
        tp.Union[list["dict_pack_spec_t"], "dict_pack_spec_t"]
    ]

pack_spec_t = tp.Union[list[dict_pack_spec_t], dict_pack_spec_t]


def mcq_enum_items(
        content: mcq_content_t,
        parent: mcq_content_t | None = None
) -> tp.Generator[tuple[mcq_content_t, None | mcq_content_t]]:
    yield content, parent
    if content["children"] is not None:
        for c in content["children"]:
            yield from mcq_enum_items(c, content)


def check_pack_spec(spec: str) -> pack_spec_t:
    try:
        parsed = json.loads(spec)
        TypeAdapter(pack_spec_t).validate_python(parsed)
    except (ValidationError, json.decoder.JSONDecodeError) as ex:
        raise ValueError from ex
    return tp.cast(pack_spec_t, parsed)


def check_mcq_content(spec: str) -> mcq_content_t:
    try:
        parsed = json.loads(spec)
        TypeAdapter(mcq_content_t).validate_python(parsed)
    except (ValidationError, json.decoder.JSONDecodeError) as ex:
        raise ValueError from ex
    return tp.cast(mcq_content_t, parsed)


def check_item_mdata(mdata: str) -> item_mdata_t:
    try:
        TypeAdapter(item_mdata_t).validate_python(mdata)
    except ValidationError as ex:
        raise ValueError from ex
    return tp.cast(item_mdata_t, mdata)
