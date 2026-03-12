#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.project import router
from webamc.util import fmt, io
from webamc import project


def page(
        ctx: context.Context,
        args: router.args_project_code_t
) -> fa.Response:
    trs_files = list()
    trs_logs = list()
    for f, s, d in project.list_files(
            session.usr_code(ctx),
            args["project_code"]
    ):
        ext = io.get_file_extension(f)
        try:
            doc_types: dict[str, types.static_img_t] = {
                ".pdf": "doc-pdf",
                ".ods": "doc-table",
                ".zip": "doc-archive"
            }
            png = doc_types[ext]
        except KeyError:
            png = "doc-text"
        href = base.mkuri(
            "/project/page/get-file",
            project_code=args["project_code"],
            file_name=f
        )
        img = base.static_img(png, title=f, href=href)
        tr = he.Tr(
            he.Td(img),
            he.Td(he.Str(f)),
            he.Td(he.Str(format(s, ",d")), style="text-align: right;"),
            he.Td(he.Str(fmt.fmt_datetime(d)))
        )
        if ext == ".log":
            trs_logs.append(tr)
        else:
            trs_files.append(tr)

    elements: list[he.Element] = list()
    for txt, trs in [
            ("name_files", trs_files),
            ("name_logs", trs_logs)
    ]:
        elements.append(he.H2(he.Txt(txt)))
        if trs == list():
            elements.append(he.Txt("seq_no_available_file"))
        else:
            elements.append(he.Table(*trs, class_="table-form"))

    return fa.responses.HTMLResponse(str(he.ElementList(*elements)))
