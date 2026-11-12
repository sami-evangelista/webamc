from webamc.www.all import *


router = fa.APIRouter()


@router.get("/project/page/main")
def page_main(req: fa.Request, prj_id: tp.Optional[int] = None) -> fa.Response:
    from .page import main
    with context.Context(req) as ctx:
        return main.page(ctx, prj_id)


@router.post("/project/page/project")
def page_project(req: fa.Request, args: types.args_oper_t) -> fa.Response:
    from .page import project
    with context.Context(req) as ctx:
        return project.page(ctx, args)


@router.get("/project/page/manual-association")
def page_manual_association(req: fa.Request, prj_id: int) -> fa.Response:
    from .page import manual_association
    with context.Context(req) as ctx:
        return manual_association.page(ctx, prj_id)


@router.get("/project/page/get-file")
def page_get_file(
        req: fa.Request,
        prj_id: int,
        file_name: str
) -> fa.Response:
    from .page import get_file
    with context.Context(req) as ctx:
        return get_file.page(ctx, prj_id, file_name)


@router.post("/project/oper/upload")
def oper_upload(
        req: fa.Request,
        prj_id: int = fa.Form(...),
        action: types.action_t = fa.Form(...),
        file_content: fa.UploadFile = fa.File(...)
) -> fa.Response:
    from .oper import upload
    with context.Context(req) as ctx:
        return upload.data(ctx, prj_id, action, file_content)


@router.post("/project/oper/action")
def oper_action(req: fa.Request, args: types.args_oper_t) -> fa.Response:
    from .oper import action
    with context.Context(req) as ctx:
        return action.data(ctx, args)


@router.post("/project/oper/get-status")
def oper_get_status(req: fa.Request, args: types.args_oper_t) -> fa.Response:
    from .oper import get_status
    with context.Context(req) as ctx:
        return get_status.data(ctx, args)
