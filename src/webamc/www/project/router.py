#!/usr/bin/env python3

from webamc.www.all import *
from webamc import project as proj


router = fa.APIRouter()

args_oper_action_t = tp_ext.TypedDict(
    "args_oper_action_t", {
        "action": proj.action_t,
        "project_code": str,
        "action_params": proj.action_params_t
    }
)
args_page_manual_association_t = tp_ext.TypedDict(
    "args_page_manual_association_t", {
        "project_code": str,
        "action_params": proj.action_params_t
    }
)
args_project_code_t = tp_ext.TypedDict(
    "args_project_code_t", {
        "project_code": str
    }
)


@router.get("/project/page/main")
def route_project_page_main(req: fa.Request) -> fa.Response:
    from .page import main
    ctx = context.Context(req)
    return main.page(ctx)


@router.get("/project/page/inbox")
def route_project_page_inbox(req: fa.Request) -> fa.Response:
    from .page import inbox
    ctx = context.Context(req)
    return inbox.page(ctx)


@router.post("/project/page/project")
def route_project_page_project(
        req: fa.Request,
        args: args_project_code_t
) -> fa.Response:
    from .page import project
    ctx = context.Context(req)
    return project.page(ctx, args)


@router.post("/project/page/files")
def route_project_page_files(
        req: fa.Request,
        args: args_project_code_t
) -> fa.Response:
    from .page import files
    ctx = context.Context(req)
    return files.page(ctx, args)


@router.get("/project/page/get-file")
def route_project_page_get_file(
        req: fa.Request,
        project_code: str,
        file_name: str
) -> fa.Response:
    from .page import get_file
    ctx = context.Context(req)
    return get_file.page(ctx, project_code, file_name)


@router.get("/project/page/get-mail-pdf")
def route_project_page_get_mail_pdf(
        req: fa.Request,
        usr_code: str,
        project_code: str
) -> fa.Response:
    from .page import get_mail_pdf
    ctx = context.Context(req)
    return get_mail_pdf.page(ctx, usr_code, project_code)


@router.post("/project/page/manual-association")
def route_project_page_manual_association(
        req: fa.Request,
        args: args_page_manual_association_t
) -> fa.Response:
    from .page import manual_association
    ctx = context.Context(req)
    return manual_association.page(ctx, args)


@router.post("/project/oper/upload")
def route_project_oper_upload(
        req: fa.Request,
        file_id: proj.file_id_t = fa.Form(...),
        file_content: fa.UploadFile = fa.File(...),
        project_code: str = fa.Form(...)
) -> fa.Response:
    from .oper import upload
    ctx = context.Context(req)
    return upload.data(ctx, file_id, file_content, project_code)


@router.post("/project/oper/action")
def route_project_oper_action(
        req: fa.Request,
        args: args_oper_action_t
) -> fa.Response:
    from .oper import action
    ctx = context.Context(req)
    return action.data(ctx, args)


@router.post("/project/oper/get-status")
def route_project_oper_get_status(
        req: fa.Request,
        args: args_project_code_t
) -> fa.Response:
    from .oper import get_status
    ctx = context.Context(req)
    return get_status.data(ctx, args)


@router.post("/project/oper/get-data")
def route_project_oper_get_data(
        req: fa.Request,
        args: args_project_code_t
) -> fa.Response:
    from .oper import get_data
    ctx = context.Context(req)
    return get_data.data(ctx, args)


@router.post("/project/oper/set-data")
def route_project_oper_set_data(
        req: fa.Request,
        args: dict[str, str]
) -> fa.Response:
    from .oper import set_data
    ctx = context.Context(req)
    return set_data.data(ctx, args)
