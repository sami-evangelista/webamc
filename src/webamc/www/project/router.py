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
def route_project_page_main(req: fa.Request, pcode: str = "") -> fa.Response:
    from .page import main
    with context.Context(req) as ctx:
        return main.page(ctx, pcode)


@router.post("/project/page/project")
def route_project_page_project(
        req: fa.Request,
        args: args_project_code_t
) -> fa.Response:
    from .page import project
    with context.Context(req) as ctx:
        return project.page(ctx, args)


@router.get("/project/page/get-file")
def route_project_page_get_file(
        req: fa.Request,
        project_code: str,
        file_name: str
) -> fa.Response:
    from .page import get_file
    ctx = context.Context(req)
    return get_file.page(ctx, project_code, file_name)


@router.post("/project/page/manual-association")
def route_project_page_manual_association(
        req: fa.Request,
        args: args_page_manual_association_t
) -> fa.Response:
    from .page import manual_association
    with context.Context(req) as ctx:
        return manual_association.page(ctx, args)


@router.post("/project/oper/upload")
def route_project_oper_upload(
        req: fa.Request,
        action: proj.action_t = fa.Form(...),
        file_content: fa.UploadFile = fa.File(...),
        project_code: str = fa.Form(...)
) -> fa.Response:
    from .oper import upload
    ctx = context.Context(req)
    return upload.data(ctx, action, file_content, project_code)


@router.post("/project/oper/action")
def route_project_oper_action(
        req: fa.Request,
        args: args_oper_action_t
) -> fa.Response:
    from .oper import action
    with context.Context(req) as ctx:
        return action.data(ctx, args)


@router.post("/project/oper/get-status")
def route_project_oper_get_status(
        req: fa.Request,
        args: args_project_code_t
) -> fa.Response:
    from .oper import get_status
    ctx = context.Context(req)
    return get_status.data(ctx, args)


@router.post("/project/oper/set-data")
def route_project_oper_set_data(
        req: fa.Request,
        args: dict[str, tp.Any]
) -> fa.Response:
    from .oper import set_data
    with context.Context(req) as ctx:
        return set_data.data(ctx, args)
