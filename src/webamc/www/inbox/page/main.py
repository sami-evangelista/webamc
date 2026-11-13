from webamc.www.all import *
from webamc.util import fmt
from webamc.db import queries


def page(ctx: context.Context) -> fa.Response:
    trs: list[list[he.Element]] = list()
    for msg, usr in queries.list_messages(ctx.dbs, session.usr_id(ctx)):
        title = fmt.fmt_title(msg.msg_title)
        if msg.msg_type == types.MESSAGE_TYPE_FILE:
            img: types.static_img_t = "doc-pdf"
            href = base.mkuri(
                "/inbox/page/msg",
                msg_id=msg.msg_id
            )
        else:
            img = "view"
            href = base.mkuri(
                "/mcq/page/form",
                mode="view",
                sub_id=msg.msg_sub
            )
        link = base.static_img(
            img,
            None,
            href=href,
            title_str=title
        )
        tr = [
            he.Str(title),
            he.Str(fmt.fmt_name(usr.usr_fst_name, usr.usr_name)),
            he.Str(fmt.fmt_datetime(msg.msg_date)),
            link
        ]
        trs.append(tr)
    if len(trs) == 0:
        body: he.Element = he.Txt("inbox_info_empty")
    else:
        cols: list[types.txt_t] = [
            "db_col_msg_title",
            "db_col_msg_from",
            "db_col_msg_date"
        ]
        body = he.mktable(trs, class_="table-solid")
        body.insert(0, he.Thead(he.Tr(*[he.Td(he.Txt(c)) for c in cols])))
    return base.page(ctx, "inbox", body)
