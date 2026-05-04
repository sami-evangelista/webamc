from webamc.www.all import *


router = fa.APIRouter()

args_oper_save_pack_t = tp_ext.TypedDict("args_oper_save_pack_t", {
    "code": str,
    "title": str,
    "pack": tp.Any
})
args_page_item_t = tp_ext.TypedDict("args_page_item_t", {
    "itm_id": int
})

args_oper_delete_instance_t = tp_ext.TypedDict(
    "args_oper_delete_instance_t", {
    "itm_id": int,
    "iti_num": int
})

@router.get("/item/oper/get-pack")
def route_oper_get_tags(req: fa.Request) -> fa.Response:
    """Route to get all tags in the database."""
    with context.Context(req) as ctx:
        from .oper import get_tags
        res = get_tags.get_all_tags(ctx)
        return fa.responses.JSONResponse(res)

@router.post("/item/oper/save-pack")
def route_oper(
        req: fa.Request,
        args: args_oper_save_pack_t
) -> fa.Response:
    from .oper import save_pack
    with context.Context(req) as ctx:
        return save_pack.data(ctx, args)


@router.post("/item/oper/submit")
def route_oper_submit(
        req: fa.Request,
        zip_file: fa.UploadFile
) -> fa.Response:
    from .oper import submit
    with context.Context(req) as ctx:
        return submit.data(ctx, zip_file)


@router.post("/item/page/database-list")
def route_page_database_list(
        req: fa.Request,
        filters: dict[str, tp.Any]
) -> fa.Response:
    from .page import database_list
    with context.Context(req) as ctx:
        return database_list.page(ctx, filters)


@router.get("/item/page/database-body")
def route_page_database_body(
        req: fa.Request,
        itm_id: int,
        iti_num: int,
) -> fa.Response:
    from .page import database_body
    with context.Context(req) as ctx:
        return database_body.page(ctx, itm_id, iti_num)


@router.post("/item/oper/delete-instance")
def route_oper_delete_instance(
        req: fa.Request,
        args: dict  
) -> fa.Response:
    with context.Context(req) as ctx:
        itm_id = args["itm_id"]
        iti_num = args["iti_num"]

        print(f"Deleting item {itm_id} | instance {iti_num}")

        from webamc.db import queries, tables
        
        # check the owner of the item
        owner = queries.get_item_owner(ctx.dbs, itm_id)
        if owner is None or owner.usr_id != session.usr_id(ctx):
            raise fa.HTTPException(status_code=403)

        # getting ids of all choices related to the question
        choices = queries.get_question_choices(ctx.dbs, itm_id)
        choice_ids = [c.cho_id for c in choices]

        # deleting all instances of these choices.
        if choice_ids:
            query_choices = sa.delete(tables.ItemInstance).where(
                sa.and_(
                    tables.ItemInstance.iti_item.in_(choice_ids),
                    tables.ItemInstance.iti_num == iti_num
                )
            )
            ctx.dbs.execute(query_choices)

        # deleting the instance of the question
        query_inst = sa.delete(tables.ItemInstance).where(
            sa.and_(
                tables.ItemInstance.iti_item == itm_id,
                tables.ItemInstance.iti_num == iti_num
            )
        )
        ctx.dbs.execute(query_inst)
        ctx.dbs.commit()
        return fa.responses.JSONResponse({"status": "ok"})

@router.get("/item/page/group")
def route_page_group(
        req: fa.Request,
        grp_id: int
) -> fa.Response:
    from .page import group
    with context.Context(req) as ctx:
        return fa.responses.HTMLResponse(str(group.page(ctx, grp_id)))


@router.get("/item/page/main")
def route_page_main(
        req: fa.Request,
        sub_page: None | str = None,
        itm_id: None | int = None
) -> fa.Response:
    from .page import database, submit_form, pack, groups
    layout: base.page_layout_t = {
        "title": "page_title_item",
        "path": "/item/page/main",
        "default": "database",
        "sub_pages": {
            "database": (False, "database", database.page),
            "submit_form": (False, "upload", submit_form.page),
            "pack": (True, "add", pack.page),
            "groups": (False, "group", groups.page)
        }
    }
    with context.Context(req) as ctx:
        session.check_logged_in(ctx)
        result = base.gen_composite_page(
            ctx, layout, sub_page, sub_page_args={"itm_id": itm_id}
        )
    return result
