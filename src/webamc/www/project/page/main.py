from webamc.www.all import *
from webamc.db import queries


def page(ctx: context.Context, prj_id: tp.Optional[int]) -> fa.Response:
    span_new = base.mkhelp(
        he.Span(he.Txt("project_new")),
        "project",
        section="help-project-new"
    )
    input_code = he.Input(name="prj_code", id_="prj_code")
    a_new = base.static_img(
        "add",
        "base_add",
        js="project_new()"
    )
    trs: list[tuple[he.Element, he.Element]] = [
        (span_new, he.ElementList(input_code, a_new))
    ]
    options = [
        he.Option(
            he.Str(p.prj_code), value=p.prj_id
        ).add_flag(
            "selected", p.prj_id == prj_id
        )
        for p in queries.list_projects(ctx.dbs, session.usr_id(ctx))
    ]
    select_projects = he.Select(
        *options,
        name="prj_id",
        id_="prj_id",
        onchange="project_load()"
    ).sort(
    ).set_data(
        "type", "integer"
    ).insert(
        0, he.Option(he.Str("-"), value="")
    )
    trs.append(
        (he.Txt("project_select"), select_projects)
    )
    table = he.mktable(trs, class_="table-form")
    div_form = he.Div(table, class_="box")
    div_project = he.Div(id_="div-project")
    js = he.Script("project_load()")
    elements = he.ElementList(div_form, div_project, js)
    return base.page(ctx, "project", elements)
