import fastapi as fa

from webamc import project
from webamc.db import tables, queries
from webamc.util import fmt
from webamc.www import context


def is_logged_in(ctx: context.Context) -> bool:
    return "usr_id" in ctx.req.session


def usr_id(ctx: context.Context) -> int:
    check_logged_in(ctx)
    return int(ctx.req.session["usr_id"])


def usr_code(ctx: context.Context) -> str:
    check_logged_in(ctx)
    return str(ctx.req.session["usr_code"])


def usr_eaddr(ctx: context.Context) -> str:
    check_logged_in(ctx)
    return str(ctx.req.session["usr_eaddr"])


def logout(ctx: context.Context) -> None:
    keys = list(ctx.req.session)
    for key in keys:
        ctx.req.session.pop(key)


def is_admin(ctx: context.Context) -> bool:
    check_logged_in(ctx)
    return bool(ctx.req.session["usr_admin_tables"] != dict())


def can_admin_table(ctx: context.Context, tbl: int | str) -> bool:
    check_logged_in(ctx)
    return any(
        int(tbl_id) == tbl if isinstance(tbl, int)
        else tbl_name == tbl
        for tbl_id, tbl_name in ctx.req.session["usr_admin_tables"].items()
    )


def usr_name(ctx: context.Context) -> str:
    check_logged_in(ctx)
    return fmt.fmt_name(
        ctx.req.session["usr_fst_name"],
        ctx.req.session["usr_name"]
    )


def usr_view_groups(ctx: context.Context) -> dict[int, str]:
    check_logged_in(ctx)
    return {
        int(grp_id): str(grp_name)
        for grp_id, grp_name in ctx.req.session["usr_view_grps"].items()
    }


def usr_submit_groups(ctx: context.Context) -> dict[int, str]:
    check_logged_in(ctx)
    return {
        int(grp_id): str(grp_name)
        for grp_id, grp_name in ctx.req.session["usr_submit_grps"].items()
    }


def has_submission_right(ctx: context.Context) -> bool:
    check_logged_in(ctx)
    return len(ctx.req.session["usr_submit_grps"]) > 0


def has_admin_right(ctx: context.Context, item: tables.Item) -> bool:
    check_logged_in(ctx)
    return item.itm_usr == usr_id(ctx)


def get_viewable_mcqs(
        ctx: context.Context
) -> list[tuple[tables.Mcq, tables.Item, tables.Usr]]:
    check_logged_in(ctx)
    return queries.get_viewable_mcqs(
        ctx.dbs, usr_id(ctx), set(usr_view_groups(ctx).keys())
    )


def active_registration(
        ctx: context.Context
) -> None | tuple[tables.Registration, tables.Exam, tables.Mcq]:
    check_logged_in(ctx)
    liste = ctx.req.session.get("reg_id")
    reg_id = liste[0] if liste is not None else None
    if reg_id is None:
        return None
    row = ctx.dbs.query(
        tables.Registration,
        tables.Exam,
        tables.Mcq
    ).where(
        (tables.Registration.reg_id == int(reg_id))
        & (tables.Registration.reg_exam == tables.Exam.exm_id)
        & (tables.Exam.exm_mcq == tables.Mcq.mcq_id)
    ).first()
    assert row is not None
    return row.tuple()


def clear_active_registration(ctx: context.Context) -> None:
    check_logged_in(ctx)
    ctx.req.session["reg_id"] = None


def img_push(ctx: context.Context, itm_id: int) -> None:
    check_logged_in(ctx)
    ctx.req.session["imgs"].append(itm_id)


def img_pushed(ctx: context.Context, itm_id: int) -> bool:
    check_logged_in(ctx)
    return itm_id in ctx.req.session["imgs"]


def init(ctx: context.Context, usr: tables.Usr) -> None:
    req = ctx.req
    req.session["usr_code"] = str(usr.usr_code)
    req.session["usr_id"] = int(usr.usr_id)
    req.session["usr_fst_name"] = str(usr.usr_fst_name)
    req.session["usr_name"] = str(usr.usr_name)
    req.session["usr_eaddr"] = str(usr.usr_eaddr)
    req.session["usr_view_grps"] = {
        int(grp.grp_id): str(grp.grp_name)
        for grp in queries.get_view_grps(ctx.dbs, usr.usr_id)
    }
    req.session["usr_submit_grps"] = {
        int(grp.grp_id): str(grp.grp_name)
        for grp in queries.get_submit_grps(ctx.dbs, usr.usr_id)
    }
    req.session["usr_admin_tables"] = {
        int(tbl.tbl_id): str(tbl.tbl_name)
        for tbl in queries.get_admin_tables(ctx.dbs, usr.usr_id)
    }
    exam_registration = queries.get_active_registration(
        ctx.dbs, req.session["usr_id"]
    )
    if exam_registration is None:
        req.session["reg_id"] = None
    else:
        exam, registration = exam_registration
        req.session["reg_id"] = [
            registration.reg_id, exam.exm_id, exam.exm_mcq
        ]
    req.session["imgs"] = list()


def check_logged_in(ctx: context.Context) -> None:
    if not is_logged_in(ctx):
        raise fa.HTTPException(status_code=404)


def check_admin(ctx: context.Context) -> None:
    check_logged_in(ctx)
    if not is_admin(ctx):
        raise fa.HTTPException(status_code=403)


def check_admin_table(ctx: context.Context, tbl: int | str) -> None:
    check_logged_in(ctx)
    if not can_admin_table(ctx, tbl):
        raise fa.HTTPException(status_code=403)


def check_active_registration(ctx: context.Context) -> None:
    check_logged_in(ctx)
    if active_registration(ctx) is None:
        raise fa.HTTPException(status_code=403)


def check_can_view_mcq(ctx: context.Context, mcq_id: int) -> None:
    check_logged_in(ctx)
    if not any(mcq.mcq_id == mcq_id for mcq, _, _ in get_viewable_mcqs(ctx)):
        raise fa.HTTPException(status_code=403)


def ne_inbox(ctx: context.Context) -> bool:
    return not project.inbox_empty(usr_code(ctx))
