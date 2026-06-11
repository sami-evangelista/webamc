from webamc.www.all import *
from webamc.db import util as db_util
from webamc.www.db import util as www_db_util


def page(
        ctx: context.Context,
        id_: str,
        col_name: str,
        col_id_name: str
) -> fa.Response:
    col = db_util.get_col(col_name)
    tbl = db_util.get_col_tbl(col)
    pkey = db_util.get_tbl_pkey(tbl)
    value = ctx.dbs.query(col).where(pkey == id_).scalar()
    elements = www_db_util.html_element(
        ctx, col, prefix=f"update-{id_}-", val=value
    )
    img_validate = base.static_img(
        "checkmark",
        "verb_validate",
        size=24,
        js=f"db_col_send_update('{tbl}', {id_}, '{col_name}', '{col_id_name}')"
    )
    img_cancel = base.static_img(
        "dismiss",
        "verb_cancel",
        size=24,
        js=f"db_col_toggle({id_}, '{col_name}', '{col_id_name}')"
    )
    tr = he.Tr(
        he.Td(*elements, style="padding: 0px; border-style: none;"),
        he.Td(img_validate, style="padding: 0px; border-style: none;"),
        he.Td(img_cancel, style="padding: 0px; border-style: none;")
    )
    el = he.ElementList(he.Table(tr))
    return fa.responses.HTMLResponse(str(el))
