from webamc.www.all import *
from webamc.db import tables
from webamc.www.db.util import get_txt_and_input


def page(ctx: context.Context, itm_id: None | int) -> he.Element:
    def get_trs() -> tp.Generator[list[he.Element]]:
        yield [base.field_label(he.Txt("word_type"))]
        yield [select_type]
        for txt, inpt in get_txt_and_input(
                ctx,
                tables.Item.itm_code,
                tables.Item.itm_title
        ):
            yield [txt]
            yield [inpt]
        yield [base.field_label(he.Txt("seq_content_type"))]
        yield [select_content_type]
    select_type = he.Select(
        he.Option(he.Txt("word_mcq"), value="mcq"),
        he.Option(he.Txt("word_exercise"), value="exe"),
        id_="itm_exe_or_mcq"
    )
    select_content_type = he.Select(
        he.Option(
            he.Txt("seq_question_pack"),
            value=str(types.ITEM_TYPE_PACK)
        ),
        he.Option(
            he.Txt("seq_exercise_list"),
            value=str(types.ITEM_TYPE_EXERCISE)
        ),
        id_="itm_type"
    ).set_data("type", "integer")
    img_validate = base.static_img(
        "checkmark",
        "word_validate",
        js="item_add()",
        class_="submit"
    )
    table = he.mktable(
        get_trs(),
        id_="table-add-item",
        class_="table-form"
    )
    result = he.Div(
        table,
        img_validate,
        class_="box"
    )
    return result
