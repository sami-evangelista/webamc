from webamc.www.all import *
from webamc.db import desc, tables
from webamc.util import fmt


def page(ctx: context.Context) -> fa.Response:
    trs: list[list[he.Element]] = list()
    for item, usr in session.get_viewable_mcqs(ctx):
        links: list[he.Element] = list()
        has_admin_right = session.has_admin_right(ctx, item)

        # links
        href = base.mkuri(
            "/mcq/page/form",
            mode="review",
            itm_id=str(item.itm_id)
        )
        a_fillin = base.static_img("edit", "word_answer", href=href)
        links.append(a_fillin)
        if has_admin_right:
            href = base.mkuri(
                "/item/page/main",
                sub_page="item_database",
                itm_id=item.itm_id
            )
            links += [
                base.static_img("settings", "word_administrate", href=href)
            ]
        fields = [
            str(item.itm_title),
            fmt.fmt_name(usr.usr_fst_name, usr.usr_name),
            fmt.fmt_datetime(item.itm_date)
        ]
        tds: list[he.Element] = [he.Str(field) for field in fields]
        tds.append(he.ElementList(*links))
        trs.append(tds)
    body: he.Element
    if trs == list():
        body = he.P(he.Txt("info_no_mcq_available"))
    else:
        cols = [
            tables.Item.itm_title,
            tables.Item.itm_usr,
            tables.Item.itm_date
        ]
        tds = [he.Td(he.Txt(desc.col_desc(c))) for c in cols]
        table = he.mktable(trs, class_="table-solid")
        table.insert(0, he.Thead(he.Tr(*tds)))
        body = table
    return base.page(ctx, "index", body)
