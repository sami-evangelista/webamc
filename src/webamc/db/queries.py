#!/usr/bin/env python3

from sqlalchemy.orm.session import Session
from sqlalchemy.orm.query import Query

from webamc.all import *
from . import tables


def get_grps(
        dbs: Session,
        usr_id: int
) -> list[tuple[tables.Grp, tables.UsrGrp]]:
    query = dbs.query(
        tables.Grp,
        tables.UsrGrp
    ).where(
        (tables.UsrGrp.ugp_usr == usr_id)
        & (tables.UsrGrp.ugp_grp == tables.Grp.grp_id)
    )
    return [row.tuple() for row in query]


def get_viewable_mcqs(
        dbs: Session,
        usr_id: int,
        grp_ids: set[int]
) -> list[tuple[tables.Mcq, tables.Item, tables.Usr]]:
    # An item is selected if
    # (1) it is owned by the user
    # or (2.1) the mcq is in review mode
    #    and (2.2) the mcq is visible
    #    and (2.3) the user has view access on one of the groups
    #              the mcq belongs to
    query = dbs.query(
        tables.Mcq,
        tables.Item,
        tables.Usr
    ).where(
        (tables.Mcq.mcq_id == tables.Item.itm_id)
        & (tables.Item.itm_usr == tables.Usr.usr_id)
        & (
            (tables.Item.itm_usr == usr_id)  # (1)
            | (
                (tables.Mcq.mcq_mode == types.MCQ_MODE_REVIEW) # (2.1)
                & (tables.Item.itm_visible) # (2.2)
                & (
                    tables.Mcq.mcq_id.in_(
                        dbs.query(
                            tables.McqGrp.mgp_mcq
                        ).where(
                            tables.McqGrp.mgp_grp.in_(grp_ids)
                        )
                    )  # (2.3)
                )
            )
        )
    ).order_by(
        tables.Item.itm_title
    )
    return [row.tuple() for row in query]


def get_question(
        dbs: Session,
        qst_id: int
) -> tables.Question:
    result = dbs.query(tables.Question).where(
        tables.Question.qst_id == qst_id
    ).first()
    assert result is not None
    return result


def get_pack(
        dbs: Session,
        pak_id: int
) -> tables.Pack:
    result = dbs.query(tables.Pack).where(tables.Pack.pak_id == pak_id).first()
    assert result is not None
    return result


def get_active_registration(
        dbs: Session,
        usr_id: int
) -> None | tuple[tables.Exam, tables.Registration]:
    now = datetime.datetime.now()
    exam_registration = dbs.query(
        tables.Exam,
        tables.Registration
    ).where(
        (tables.Exam.exm_start <= now)
        & (tables.Registration.reg_exam == tables.Exam.exm_id)
        & (tables.Registration.reg_usr == usr_id)
    ).first()
    if exam_registration is None:
        return None
    exam, registration = exam_registration.tuple()
    if tables.Exam.end_time(exam) >= now:
        return exam, registration
    return None


def get_grp_tree(dbs: Session, grp_id: int) -> set[int]:
    result = {grp_id}
    todo = {grp_id}
    while todo != set():
        stmt = dbs.query(
            tables.Grp.grp_id
        ).where(
            tables.Grp.grp_parent.in_(todo)
        )
        todo = {grp[0] for grp in stmt.all() if grp not in result}
        result = result.union(todo)
    return result


def get_grps_usrs(
        dbs: Session,
        grp_ids: set[int],
        right: types.usr_right_t
) -> tp.Iterator[tables.Usr]:
    query = dbs.query(
        tables.Usr
    ).where(
        (tables.Grp.grp_id.in_(grp_ids))
        & (tables.Grp.grp_id == tables.UsrGrp.ugp_grp)
        & (tables.Usr.usr_id == tables.UsrGrp.ugp_usr)
        & (tables.UsrGrp.ugp_right == right)
    ).order_by(
        tables.Usr.usr_code
    )
    yield from query.all()


def get_usr_exams(
        dbs: Session,
        usr_id: int
) -> list[tuple[tables.Mcq, tables.Item, tables.Exam]]:
    query = dbs.query(
        tables.Mcq,
        tables.Item,
        tables.Exam
    ).where(
        (tables.Exam.exm_mcq == tables.Mcq.mcq_id)
        & (tables.Exam.exm_mcq == tables.Item.itm_id)
        & (tables.Item.itm_usr == usr_id)
    ).order_by(
        tables.Exam.exm_start.desc()
    )
    return [row.tuple() for row in query]


def get_exam_registrations(
        dbs: Session,
        exm_id: int
) -> list[tuple[tables.Usr, tables.Registration]]:
    query = dbs.query(
        tables.Usr,
        tables.Registration
    ).where(
        (tables.Registration.reg_exam == exm_id)
        & (tables.Registration.reg_usr == tables.Usr.usr_id)
    )
    return [row.tuple() for row in query.all()]


def get_ticket(
        dbs: Session,
        ticket: str
) -> None | tuple[tables.Ticket, tables.Usr]:
    query = dbs.query(
        tables.Ticket,
        tables.Usr
    ).where(
        (tables.Ticket.tkt_value == ticket)
        & (tables.Ticket.tkt_usr == tables.Usr.usr_id)
        & (tables.Ticket.tkt_deadline > datetime.datetime.now())
    )
    row = query.first()
    if row is None:
        return None
    return row.tuple()


def gen_pack_questions(
        dbs: Session,
        item: tables.Item,
        usr_id: int,
        not_in: set[int]
) -> list[tables.Item]:
    def traverse(spec: types.pack_spec_t) -> Query[tables.Item]:
        if isinstance(spec, list):
            result: Query[tables.Item] = traverse(spec[0])
            for c in spec[1:]:
                result = result.union(traverse(c))

            print(result)
            return result
        oper = spec.get("op", "all")
        if oper == "all":
            return dbs.query(
                tables.Item
            ).where(
                tables.Item.itm_visible
                & (tables.Item.itm_id == tables.Question.qst_id)
                & (tables.Item.itm_usr == usr_id)
                & (tables.Item.itm_standalone
                   | (tables.Item.itm_parent == None))
                & (tables.Item.itm_id.not_in(not_in))
            )
        all_op: types.pack_spec_t ={"op": "all"}
        content: types.pack_spec_t = spec.get("content", all_op)
        arg: tp.Any = spec.get("arg")
        rev: bool = spec.get("rev", False)
        result = traverse(content)
        if oper == "shuf":
            return result.order_by(sa.func.random())
        if oper == "head":
            return result.limit(int(arg))
        if oper == "sort":
            try:
                by = {
                    "difficulty": tables.Item.itm_difficulty,
                    "code": tables.Item.itm_code
                }[str(arg)]
            except KeyError:
                pass
            else:
                return result.order_by(by.desc() if rev else by)
        if oper == "with-code":
            return result.where(
                tables.Item.itm_code.in_(arg) if not rev
                else tables.Item.itm_code.not_in(arg)
            )
        if oper == "with-difficulty":
            return result.where(
                tables.Item.itm_difficulty.in_(arg) if not rev
                else tables.Item.itm_difficulty.not_in(arg)
            )
        if oper == "with-tag":
            sub = dbs.query(
                tables.Item.itm_id.distinct()
            ).where(
                (tables.Item.itm_id == tables.ItemTag.itg_item)
                & (tables.Tag.tag_id == tables.ItemTag.itg_tag)
                & (tables.Tag.tag_name.in_(arg))
            )
            return result.where(
                tables.Item.itm_id.in_(sub) if not rev
                else tables.Item.itm_id.not_in(sub)
            )
        return result
    assert item.itm_type == types.ITEM_TYPE_PACK
    pack = get_pack(dbs, item.itm_id)
    spec = json.loads(pack.pak_spec)
    query = traverse(spec)

    return traverse(spec).all()


def get_submission_choices(
        dbs: Session,
        sub_id: int
) -> list[tables.Choice]:
    return dbs.query(
        tables.Choice
    ).where(
        (tables.Answer.ans_submission == sub_id)
        & (tables.Answer.ans_item == tables.Choice.cho_id)
    ).all()


def get_children(dbs: Session, itm_id: int) -> list[tables.Item]:
    return dbs.query(
        tables.Item
    ).where(
        tables.Item.itm_parent == itm_id
    ).order_by(
        tables.Item.itm_order
    ).all()


def get_item(dbs: Session, itm_id: int) -> tables.Item:
    result = dbs.query(tables.Item).where(tables.Item.itm_id == itm_id).first()
    assert result is not None
    return result


def get_item_mcq(dbs: Session, itm_id: int) -> None | tables.Mcq:
    return dbs.query(tables.Mcq).where(tables.Mcq.mcq_id == itm_id).first()


def get_mcq_grps(dbs: Session, mcq_id: int) -> list[tables.Grp]:
    return dbs.query(
        tables.Grp
    ).where(
        (tables.McqGrp.mgp_mcq == mcq_id)
        & (tables.McqGrp.mgp_grp == tables.Grp.grp_id)
    ).order_by(
        tables.Grp.grp_name
    ).all()


def get_question_choices(dbs: Session, qst_id: int) -> list[tables.Choice]:
    return dbs.query(
        tables.Choice
    ).where(
        (tables.Item.itm_parent == qst_id)
        & (tables.Item.itm_id == tables.Choice.cho_id)
    ).order_by(
        tables.Item.itm_order
    ).all()


def get_item_owner(dbs: Session, itm_id: int) -> None | tables.Usr:
    return dbs.query(
        tables.Usr
    ).where(
        (tables.Item.itm_id == itm_id)
        & (tables.Item.itm_usr == tables.Usr.usr_id)
    ).first()


def _get_grps_loop(
        dbs: Session,
        usr_id: int,
        right: types.usr_right_t,
        get_next: tp.Callable[[list[int]], list[int]]
) -> list[tables.Grp]:
    result = set(
        dbs.query(
            tables.Grp
        ).where(
            (tables.UsrGrp.ugp_usr == usr_id)
            & (tables.UsrGrp.ugp_right == right)
            & (tables.UsrGrp.ugp_grp == tables.Grp.grp_id)
        ).all()
    )
    todo: list[int] = list(grp.grp_id for grp in result)
    while todo != list():
        query = dbs.query(
            tables.Grp
        ).where(
            tables.Grp.grp_id.in_(get_next(todo))
        )
        new = {row for row in query.all() if row not in result}
        result = result.union(new)
        todo = list(grp.grp_id for grp in new)
    return list(sorted(result, key=lambda grp: grp.grp_name))


def get_view_grps(dbs: Session, usr_id: int) -> list[tables.Grp]:
    def get_next(todo: list[int]) -> list[int]:
        return [
            row[0] for row in dbs.query(
                tables.Grp.grp_parent
            ).where(
                tables.Grp.grp_id.in_(todo)
            ).all()
        ]
    return _get_grps_loop(dbs, usr_id, types.USR_RIGHT_VIEW, get_next)


def get_submit_grps(dbs: Session, usr_id: int) -> list[tables.Grp]:
    def get_next(todo: list[int]) -> list[int]:
        return [
            row[0] for row in dbs.query(
                tables.Grp.grp_id
            ).where(
                tables.Grp.grp_parent.in_(todo)
            ).all()
        ]
    return _get_grps_loop(dbs, usr_id, types.USR_RIGHT_SUBMIT, get_next)


def get_item_tags(dbs: Session, itm_id: int) -> list[tables.Tag]:
    return dbs.query(
        tables.Tag
    ).where(
        (tables.ItemTag.itg_item == itm_id)
        & (tables.ItemTag.itg_tag == tables.Tag.tag_id)
    ).order_by(
        tables.Tag.tag_name
    ).all()


def get_mcq(
        dbs: Session,
        mcq_id: int
) -> None | tuple[tables.Mcq, tables.Item]:
    result = dbs.query(
        tables.Mcq,
        tables.Item
    ).where(
        (tables.Mcq.mcq_id == mcq_id)
        & (tables.Mcq.mcq_id == tables.Item.itm_id)
    ).first()
    if result is None:
        return None
    return result.tuple()


def get_tbl(dbs: Session, tbl_id: int) -> None | tables.Tbl:
    return dbs.query(tables.Tbl).where(tables.Tbl.tbl_id == tbl_id).first()


def get_admin_tables(dbs: Session, usr_id: int) -> list[tables.Tbl]:
    return dbs.query(
        tables.Tbl
    ).where(
        (tables.Admin.adm_usr == usr_id)
        & (tables.Tbl.tbl_id == tables.Admin.adm_tbl)
    ).order_by(
        tables.Tbl.tbl_name
    ).all()


def get_img(dbs: Session, itm_id: int) -> bytes | None:
    item = dbs.query(
        tables.Item
    ).where(
        tables.Item.itm_id == itm_id
    ).first()
    if item is None:
        return None
    return item.itm_img


def get_usr_grps(
        dbs: Session,
        usr: int,
        right: types.usr_right_t
) -> list[tables.Grp]:
    return dbs.query(
        tables.Grp
    ).where(
        (tables.Usr.usr_id == usr)
        & (tables.Usr.usr_id == tables.UsrGrp.ugp_usr)
        & (tables.Grp.grp_id == tables.UsrGrp.ugp_grp)
        & (tables.UsrGrp.ugp_right == right)
    ).order_by(
        tables.Grp.grp_name
    ).all()


def get_grp_sub_grps(dbs: Session, grp_id: int) -> list[tables.Grp]:
    return dbs.query(
        tables.Grp
    ).where(
        tables.Grp.grp_parent == grp_id
    ).order_by(
        tables.Grp.grp_name
    ).all()


def get_usr_by_cas_auth(dbs: Session, login: str) -> None | tables.Usr:
    return dbs.query(
        tables.Usr
    ).where(
        (tables.CasAuth.cas_enabled)
        & (tables.CasAuth.cas_login == login)
        & (tables.CasAuth.cas_usr == tables.Usr.usr_id)
    ).first()


def get_usr(dbs: Session, usr_id: int) -> None | tables.Usr:
    return dbs.query(tables.Usr).where(tables.Usr.usr_id == usr_id).first()
