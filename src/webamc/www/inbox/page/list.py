from webamc.www.all import *
from webamc.util import fmt
from webamc.db import queries


def page(ctx: context.Context) -> fa.Response:
    trs: list[he.Element] = list()
    for msg, usr in queries.list_messages(ctx.dbs, session.usr_id(ctx)):
        title = fmt.fmt_title(msg.msg_title)
        href = base.mkuri("/inbox/page/msg", msg_id=msg.msg_id)
        img = he.Img(
            src=base.static_img_src("doc-pdf"),
            class_="btn",
            onclick=f"base_relocate('{href}')",
            title=title,
            alt=title
        )
        tr = he.Tr(
            he.Td(he.Str(title)),
            he.Td(he.Str(fmt.fmt_name(usr.usr_fst_name, usr.usr_name))),
            he.Td(he.Str(fmt.fmt_datetime(msg.msg_date))),
            he.Td(img)
        )
        trs.append(tr)
    if trs == list():
        elem: he.Element = he.Txt("info_no_mcq_available")
    else:
        cols: list[types.txt_t] = ["name_title", "name_sender", "name_date"]
        trs.insert(0, he.Thead(he.Tr(*[he.Td(he.Txt(c)) for c in cols])))
        elem = he.Table(*trs, class_="solid-table")
    return base.page(ctx, "page_title_inbox", elem)
