from webamc.www.all import *
from webamc.db import util as db_util, desc
from webamc.util import fmt


def page(ctx: context.Context) -> fa.Response:
    trs: list[he.Element] = list()
    for mcq, item, usr in session.get_viewable_mcqs(ctx):
        links: list[he.Element] = list()
        has_admin_right = session.has_admin_right(ctx, item)

        # links
        href = base.mkuri("/mcq/page/form", mcq_id=str(mcq.mcq_id))
        a_fillin = base.static_img("edit", "verb_answer", href=href)
        links.append(a_fillin)
        if has_admin_right:
            href = base.mkuri(
                "/item/page/main", sub_page="database", itm_id=item.itm_id
            )
            links += [
                base.static_img("settings", "verb_administrate", href=href)
            ]
        fields = [
            str(item.itm_title),
            fmt.fmt_name(usr.usr_fst_name, usr.usr_name),
            fmt.fmt_datetime(item.itm_date)
        ]
        tds = [he.Td(he.Str(field)) for field in fields]
        tds.append(he.Td(*links))
        trs.append(he.Tr(*tds))
    body: he.Element
    if trs == list():
        body = he.P(he.Txt("info_no_mcq_available"))
    else:
        cols = [
            db_util.get_col(c) for c in ["itm_title", "itm_usr", "itm_date"]
        ]
        gd = desc.col_desc
        trs.insert(0, he.Thead(he.Tr(*[he.Td(he.Txt(gd(c))) for c in cols])))
        body = he.Table(*trs, class_="solid-table")
    return base.page(
        ctx,
        str(he.Txt("page_title_index")),
        body
    )
