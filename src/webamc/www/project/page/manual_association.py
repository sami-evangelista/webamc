#!/usr/bin/env python3

from webamc.www.all import *
from webamc.www.project import router
from webamc import project


def page(
        ctx: context.Context,
        args: router.args_page_manual_association_t
) -> fa.Response:
    usr_code = session.usr_code(ctx)
    project_code = args["project_code"]
    action_params = args["action_params"]
    _, _, _, check_result = project.check_action_dependency(
        usr_code,
        project_code,
        "associate-manual-prepare"
    )
    if check_result is not None:
        codes, ids = check_result
        response: types.json_response_t = {
            "success": False,
            "msgs": [lang.txt(c) for c in codes],
            "result": ids
        }
        return fa.responses.JSONResponse(response)

    associations = project.list_associations(usr_code, project_code)
    students = project.list_students_from_csv(
        usr_code, project_code
    )
    trs: list[he.Tr] = list()
    js = list()
    first = True
    for page, copy in sorted(associations.keys()):
        manual, auto, name_file = associations[page, copy]
        tds: list[he.Td] = list()
        tds.append(he.Td(he.Str(f"{page}/{copy}")))
        if name_file is None:
            tds.append(he.Td(he.Txt("seq_no_name")))
        else:
            img_uri = base.mkuri(
                "/project/page/get-file",
                project_code=project_code,
                file_name=name_file
            )
            img = he.Img(
                src=img_uri,
                width="500px"
            )
            tds.append(he.Td(img))
        tr = he.Tr(
            *tds,
            class_="spacebefore" if not first else ""
        )
        trs.append(tr)
        first = False

        tds = list()
        options = [he.Option(he.Str(""), value="")] + [
            he.Option(he.Str(name), value=id_) for id_, name in students
        ]
        select_student = he.Select(
            *options,
            id_=f"assoc-{page}-{copy}",
            onchange=f"project_associate_manual({page}, {copy})"
        )
        tds.append(he.Td(he.Empty()))
        tds.append(he.Td(select_student))
        trs.append(he.Tr(*tds))

        assoc = manual if manual is not None else auto
        if assoc is not None:
            js += [
                f"$('#assoc-{page}-{copy}').val('{assoc}');"
            ]
    table = he.Table(*trs)
    a_close = base.static_img(
        "dismiss",
        "verb_close",
        js="project_manual_association_close()",
        style="position: absolute; top: 5px; right: 5px;"
    )
    elements = he.ElementList(
        he.H2(he.Txt("seq_manual_association")),
        a_close,
        table,
        he.Script(js)
    )
    response = {
        "success": True,
        "msgs": list(),
        "result": str(elements)
    }
    return fa.responses.JSONResponse(response)
