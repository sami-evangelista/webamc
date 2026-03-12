#!/usr/bin/env python3

from webamc.www.all import *
from webamc import project


def page(ctx: context.Context) -> fa.Response:
    input_new_project_code = he.Input(
        name="new_project_code",
        id_="new_project_code"
    )
    a_new = base.static_img(
        "add",
        "verb_add",
        js="project_new()"
    )
    options = [he.Option()]
    options += [
        he.Option(he.Str(p), value=p)
        for p, d in project.list_projects(session.usr_code(ctx))
    ]
    select_projects = he.Select(
        *options,
        name="project_code",
        id_="project_code",
        onchange="project_load_project()"
    )
    table = he.Table(
        he.Tr(
            he.Td(he.Txt("seq_new_project")),
            he.Td(input_new_project_code),
            he.Td(a_new)
        ),
        he.Tr(
            he.Td(he.Txt("seq_select_a_project")),
            he.Td(select_projects),
            he.Td()
        ),
        class_="table-form"
    )
    div_form = he.Div(
        table,
        class_="box"
    )
    div_project = he.Div(
        id_="div-project"
    )
    elements = he.ElementList(div_form, div_project)
    return base.page(
        ctx,
        str(he.Txt("page_title_project_main")),
        elements
    )
