#!/usr/bin/env python3

from webamc.www.all import *
from webamc.util import fmt
from webamc import project


def page(ctx: context.Context) -> fa.Response:
    trs = list()
    for data in project.list_inbox(session.usr_eaddr(ctx)):
        href = base.mkuri(
            "/project/page/get-mail-pdf",
            usr_code=data["sender"],
            project_code=data["project"]
        )
        a = he.A(
            he.Str(data["title"]),
            href=href
            
        )
        tr = he.Tr(
            he.Td(he.Str(fmt.fmt_datetime(data["date"]))),
            he.Td(a)
        )
        trs.append(tr)
    table = he.Table(*trs, class_="table-form")
    return base.page(
        ctx,
        lang.txt("page_title_project_inbox"),
        table
    )
