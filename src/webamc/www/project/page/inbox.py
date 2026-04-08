from webamc.www.all import *
from webamc.util import fmt
from webamc.db import desc
from webamc import project


def page(ctx: context.Context) -> fa.Response:
    trs: list[he.Element] = list()
    for data in project.list_inbox(session.usr_code(ctx)):
        href = base.mkuri(
            "/project/page/get-mail-pdf",
            usr_code=data["sender"],
            usr_name=data["sender_name"],
            project_code=data["project"]
        )
        img = he.Img(
            src=base.static_img_src("doc-pdf"),
            class_="btn",
            onclick=f"base_relocate('{href}')",
            title=data["title"],
            alt=data["title"]
        )
        tr = he.Tr(
            he.Td(he.Str(data["title"])),
            he.Td(he.Str(data["sender_name"])),
            he.Td(he.Str(fmt.fmt_datetime(data["date"]))),
            he.Td(img)
        )
        trs.append(tr)
    if trs == list():
        elem: he.Element = he.Txt("info_no_mcq_available")
    else:
        cols: list[types.txt_t] = ["name_title", "name_sender", "name_date"]
        gd = desc.col_desc
        trs.insert(0, he.Thead(he.Tr(*[he.Td(he.Txt(c)) for c in cols])))
        elem = he.Table(*trs, class_="solid-table")
    return base.page(ctx, "page_title_project_inbox", elem)
