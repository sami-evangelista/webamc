from webamc import project
from webamc.www.all import *
from webamc.www.project import util


def page(ctx: context.Context, prj_id: int) -> fa.Response:
    prj = util.get_project(ctx, prj_id)
    associations = project.list_associations(prj)
    usrs = project.list_usrs(ctx.dbs, prj)
    trs: list[he.Tr] = list()
    js = list()
    for idx, (pg, copy) in enumerate(sorted(associations.keys())):
        manual, auto, name_file = associations[pg, copy]

        # first row with image file
        tds = [he.Td(he.Str(f"{pg}/{copy}"))]
        if name_file is None:
            tds.append(he.Td(he.Txt("project_no_name_file")))
        else:
            img_uri = base.mkuri(
                "/project/page/get-file",
                prj_id=prj.prj_id,
                file_name=str(name_file)
            )
            img = he.Img(
                src=img_uri,
                width="500px"
            )
            tds.append(he.Td(img))
        tr = he.Tr(
            *tds,
            class_="spacebefore" if not idx > 0 else ""
        )
        trs.append(tr)

        # second row with user select 
        options = [
            he.Option(
                he.Str(u[1].fmt()),
                value=u[1].usr_code if u[0] is None else u[0].uat_value
            )
            for u in usrs
        ]
        select_user = he.Select(
            *options,
            id_=f"assoc-{pg}-{copy}",
            onchange=f"project_associate_manual({pg}, {copy})"
        ).sort()
        select_user.insert(0, he.Option(he.Str("-"), value=""))
        tds = [
            he.Td(he.Empty()),
            he.Td(select_user)
        ]
        trs.append(he.Tr(*tds))
        assoc = manual if manual is not None else auto
        if assoc is not None:
            js.append(f"$('#assoc-{pg}-{copy}').val('{assoc}');")

    table = he.Table(*trs)
    a_close = base.static_img(
        "dismiss",
        "base_close",
        js="project_manual_association_close()",
        style="position: absolute; top: 5px; right: 5px;"
    )
    elements = he.ElementList(
        he.H2(he.Txt("project_manual_association")),
        a_close,
        table,
        he.Script(js)
    )
    return fa.responses.HTMLResponse(str(elements))
