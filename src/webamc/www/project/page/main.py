from webamc.www.all import *
from webamc import project


def page(ctx: context.Context, pcode: str = "") -> fa.Response:
    span_new = base.mkhelp(
        he.Span(he.Txt("seq_new_project")),
        "seq_new_project",
        "project_new"
    )
    input_code = he.Input(name="new_project_code", id_="new_project_code")
    a_new = base.static_img("add", "verb_add", js="project_new()")
    tr = he.Tr(
        he.Td(span_new),
        he.Td(input_code),
        he.Td(a_new)
    )
    trs = [tr]
    projects = project.Project.list_projects(session.usr_code(ctx))
    if len(projects) > 0:
        options = [
            he.Option(
                he.Str(p),
                value=p
            ).add_flag(
                "selected",
                p == pcode
            )
            for p, d in projects
        ]
        select_projects = he.Select(
            *options,
            name="project_code",
            id_="project_code",
            onchange="project_load_project()"
        )
        tr = he.Tr(
            he.Td(he.Txt("seq_select_a_project")),
            he.Td(select_projects),
            he.Td()
        )
        trs.append(tr)
    table = he.Table(*trs, class_="table-form")
    div_form = he.Div(table, class_="box")
    div_project = he.Div(id_="div-project")
    js = he.Script("project_load_project()")
    elements = he.ElementList(div_form, div_project, js)
    return base.page(ctx, "page_title_project_main", elements)
