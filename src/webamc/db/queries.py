import datetime
from sqlalchemy.orm import aliased
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.query import Query

from webamc.all import *
from . import tables


class submission_result_t(tp_ext.TypedDict):
    sub: tables.Submission
    items: set[tables.Item]  # all items that appear in the submission
    qst_answers: dict[tables.Item, set[tables.Item]]  # choices made for a qst
    qst_score: dict[tables.Item, int]  # score for each question
    qst_max_score: dict[tables.Item, int]  # max score for each question
    cho_correct: dict[tables.Item, bool]  # correct choices
class exam_usr_result_t(tp_ext.TypedDict):
    usr: tables.Usr
    reg: tables.Registration
    sub_result: None | submission_result_t
exam_result_t = tp.Iterator[exam_usr_result_t]


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
    return [row._tuple() for row in query]


def get_viewable_mcqs(
        dbs: Session,
        usr_id: int,
        grp_ids: set[int]
) -> list[tuple[tables.Item, tables.Usr]]:
    """Return the list of MCQs the user identified by usr_id can view.

    grp_ids is the set of group ids the user has view access on.

    An MCQ is selected if (1) it is owned by the user or (2.1) the mcq
    is in review mode and (2.2) the mcq is visible and (2.3) the user
    has view access on one of the groups the MCQ belongs to.

    """
    query = dbs.query(
        tables.Item,
        tables.Usr
    ).where(
        tables.Item.itm_is_mcq
        & (tables.Item.itm_usr == tables.Usr.usr_id)
        & (
            (tables.Item.itm_usr == usr_id)  # (1)
            | (
                (tables.Item.itm_mcq_mode == types.MCQ_MODE_REVIEW)  # (2.1)
                & (tables.Item.itm_visible)  # (2.2)
                & (
                    tables.Item.itm_id.in_(
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
    return [row._tuple() for row in query]


def get_active_registration(
        dbs: Session,
        usr_id: int
) -> None | tuple[tables.Exam, tables.Registration]:
    now = datetime.datetime.now()

    # getting every exam of this student
    exam_registrations = dbs.query(
        tables.Exam,
        tables.Registration
    ).where(
        (tables.Exam.exm_start <= now)
        & (tables.Registration.reg_exam == tables.Exam.exm_id)
        & (tables.Registration.reg_usr == usr_id)
    ).all()

    # getting the ongoing examd
    for row in exam_registrations:
        exam, registration = row._tuple()
        if exam.end_time() >= now:
            return exam, registration

    return None


def get_grp_tree(dbs: Session, grp_id: int) -> set[int]:
    """Return the group and all its tree."""
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
) -> tp.Generator[tables.Usr]:
    query = dbs.query(
        tables.Usr
    ).where(
        (tables.Grp.grp_id.in_(grp_ids))
        & (tables.Grp.grp_id == tables.UsrGrp.ugp_grp)
        & (tables.Usr.usr_id == tables.UsrGrp.ugp_usr)
        & (tables.UsrGrp.ugp_right == right)
    ).order_by(
        tables.Usr.usr_name,
        tables.Usr.usr_fst_name
    )
    yield from query.all()


def is_in_grps(
        dbs: Session,
        usr_id: int,
        grp_ids: set[int],
        right: types.usr_right_t
) -> bool:
    query = dbs.query(
        tables.UsrGrp
    ).where(
        (tables.UsrGrp.ugp_usr == usr_id)
        & (tables.UsrGrp.ugp_grp.in_(grp_ids))
        & (tables.UsrGrp.ugp_right == right)
    )
    return query.first() is not None


def get_usr_exams(
        dbs: Session,
        usr_id: int
) -> list[tuple[tables.Item, tables.Exam]]:
    query = dbs.query(
        tables.Item,
        tables.Exam
    ).where(
        (tables.Exam.exm_mcq == tables.Item.itm_id)
        & (tables.Item.itm_usr == usr_id)
    ).order_by(
        tables.Exam.exm_start.desc()
    )
    return [row._tuple() for row in query]


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
    return [row._tuple() for row in query.all()]


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
    return row._tuple()


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
            return result
        oper = spec.get("op", "all")
        if oper == "all":
            return dbs.query(
                tables.Item
            ).where(
                tables.Item.itm_visible
                & (tables.Item.itm_type == types.ITEM_TYPE_QUESTION)
                & (tables.Item.itm_qst_standalone)
                & (tables.Item.itm_usr == usr_id)
                & (tables.Item.itm_id.not_in(not_in))
            )
        all_op: types.pack_spec_t = {"op": "all"}
        content: types.pack_spec_t = spec.get("content", all_op)
        arg: tp.Any = spec.get("arg")
        rev: bool = spec.get("rev", False)
        result = traverse(content)
        if oper == "shuf":
            o = sa.func.random()
            return result.order_by(o)
        if oper == "head":
            return result.limit(int(arg))
        if oper == "by-tag":
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
    assert item.itm_pack_spec is not None
    spec = json.loads(item.itm_pack_spec)
    return traverse(spec).all()


def get_submission_choices(
        dbs: Session,
        sub: tables.Submission
) -> list[tables.Item]:
    return dbs.query(
        tables.Item
    ).join(
        tables.ItemInstance,
        tables.ItemInstance.iti_item == tables.Item.itm_id
    ).join(
        tables.Answer,
        tables.Answer.ans_instance == tables.ItemInstance.iti_id
    ).where(
        (tables.Answer.ans_submission == sub.sub_id)
        & (tables.Item.itm_type == types.ITEM_TYPE_CHOICE)
    ).all()


def get_children(
        dbs: Session,
        itm_id: int,
        child_type: None | types.item_type_t = None
) -> list[tables.Item]:
    result = dbs.query(
        tables.Item
    ).where(
        (tables.ItemRelation.itr_parent == itm_id)
        & (tables.ItemRelation.itr_child == tables.Item.itm_id)
    ).order_by(
        tables.ItemRelation.itr_order
    ).all()
    if child_type is not None:
        assert all(it.itm_type == child_type for it in result)
    return result


def get_item(dbs: Session, itm_id: int) -> tables.Item:
    result = dbs.query(tables.Item).where(tables.Item.itm_id == itm_id).first()
    assert result is not None
    return result


def get_mcq_grps(dbs: Session, itm_id: int) -> list[tables.Grp]:
    return dbs.query(
        tables.Grp
    ).where(
        (tables.McqGrp.mgp_mcq == itm_id)
        & (tables.McqGrp.mgp_grp == tables.Grp.grp_id)
    ).order_by(
        tables.Grp.grp_name
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
        get_next: tp.Callable[[list[int]], tp.Generator[int]]
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
    def get_next(todo: list[int]) -> tp.Generator[int]:
        query = dbs.query(
            tables.Grp.grp_parent
        ).where(
            tables.Grp.grp_id.in_(todo)
        )
        for row in query:
            grp_parent = row._tuple()[0]
            if grp_parent is not None:
                yield grp_parent
    return _get_grps_loop(dbs, usr_id, types.USR_RIGHT_VIEW, get_next)


def get_submit_grps(dbs: Session, usr_id: int) -> list[tables.Grp]:
    def get_next(todo: list[int]) -> tp.Generator[int]:
        query = dbs.query(
            tables.Grp.grp_id
        ).where(
            tables.Grp.grp_parent.in_(todo)
        )
        for row in query:
            yield row._tuple()[0]
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


def get_img(dbs: Session, iti_id: int, iti_uuid: str) -> bytes | None:
    instance = dbs.query(
        tables.ItemInstance
    ).where(
        (tables.ItemInstance.iti_id == iti_id)
        & (tables.ItemInstance.iti_uuid == iti_uuid)
    ).first()

    if instance is None:
        return None

    return instance.iti_img


def get_instances(dbs: Session, itm_id: int) -> list[tables.ItemInstance]:
    return dbs.query(
        tables.ItemInstance
    ).where(
        tables.ItemInstance.iti_item == itm_id
    ).order_by(
        tables.ItemInstance.iti_num
    ).all()


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


def get_student_detailed_scores(
        dbs: Session,
        exam_id: int,
        sub_id: int
) -> dict[int, float]:
    return dict()
    """
    result = dict()
    direct_items = dbs.query(tables.Item.itm_id).filter(
        tables.Item.itm_parent == exam_id
    ).all()
    parent_ids = [exam_id] + [item.itm_id for item in direct_items]
    questions = dbs.query(tables.Question).join(
        tables.Item, tables.Question.qst_id == tables.Item.itm_id
    ).filter(
        tables.Item.itm_parent.in_(parent_ids)
    ).all()
    student_choices = get_submission_choices(dbs, sub_id)
    student_checked_ids = [c.cho_id for c in student_choices]
    for qst in questions:
        choices = dbs.query(tables.Choice).join(
            tables.Item, tables.Choice.cho_id == tables.Item.itm_id
        ).filter(
            tables.Item.itm_parent == qst.qst_id
        ).all()
        correct_choice_ids = [c.cho_id for c in choices if c.cho_correct]
        if not correct_choice_ids:
            continue
        question_choice_ids = [c.cho_id for c in choices]
        student_answered_for_this_qst = [
            cid for cid in student_checked_ids if cid in question_choice_ids
        ]
        question_score = 0.0
        if student_answered_for_this_qst:
            if len(correct_choice_ids) == 1:
                if student_answered_for_this_qst[0] in correct_choice_ids:
                    question_score = 1.0
            else:
                points_per_correct = 1.0 / len(correct_choice_ids)
                q_score_temp = 0.0
                for checked_id in student_answered_for_this_qst:
                    if checked_id in correct_choice_ids:
                        q_score_temp += points_per_correct
                    else:
                        q_score_temp -= points_per_correct
                question_score = max(0.0, q_score_temp)
        result[qst.qst_id] = round(question_score, 2)
    return result
    """


def list_recipients(
        dbs: Session,
        usr_id: int,
        msg_code: str
) -> list[tables.Usr]:
    query = dbs.query(
        tables.Usr
    ).where(
        (tables.Message.msg_from == usr_id)
        & (tables.Message.msg_to == tables.Usr.usr_id)
    )
    return query.all()


def list_messages(
        dbs: Session,
        usr_id: int
) -> list[tuple[tables.Message, tables.Usr]]:
    query = dbs.query(
        tables.Message,
        tables.Usr
    ).where(
        (tables.Message.msg_to == usr_id)
        & (tables.Message.msg_from == tables.Usr.usr_id)
    ).order_by(
        tables.Message.msg_date.desc()
    )
    return [row._tuple() for row in query.all()]


def has_messages(dbs: Session, usr_id: int) -> bool:
    return dbs.query(
        tables.Message
    ).where(
        tables.Message.msg_to == usr_id
    ).first() is not None


def get_registration_submission(
        dbs: Session,
        reg: tables.Registration
) -> tables.Submission | None:
    result = dbs.query(
        tables.Submission
    ).where(
        (tables.Submission.sub_exm_registration == reg.reg_id)
        & (tables.Submission.sub_type == types.SUBMISSION_TYPE_EXAM)
    ).first()
    return result


def get_item_instance(
        dbs: Session,
        itm_id: int,
        iti_num: int
) -> None | tables.ItemInstance:
    return dbs.query(
        tables.ItemInstance
    ).where(
        (tables.ItemInstance.iti_item == itm_id)
        & (tables.ItemInstance.iti_num == iti_num)
    ).first()


def get_usr_items(
        dbs: Session,
        usr_id: int
) -> list[tables.Item]:
    return dbs.query(
        tables.Item
    ).where(
        tables.Item.itm_usr == usr_id
    ).all()


def get_submission_result(dbs: Session, sub_id: int) -> submission_result_t:
    return get_submissions_result(dbs, [sub_id])[sub_id]


def get_submissions_result(
        dbs: Session,
        sub_ids: tp.Iterable[int]
) -> dict[int, submission_result_t]:
    result: dict[int, submission_result_t] = dict()

    # query all items included in the submission
    item_alias = aliased(tables.Item)
    query = dbs.query(
        tables.Submission,
        tables.Item,
        item_alias
    ).select_from(
        tables.Submission
    ).where(
        tables.Submission.sub_id.in_(sub_ids)
    ).join(
        tables.Answer,
        tables.Answer.ans_submission == tables.Submission.sub_id
    ).join(
        tables.ItemInstance,
        tables.ItemInstance.iti_id == tables.Answer.ans_instance
    ).join(
        tables.Item,
        tables.Item.itm_id == tables.ItemInstance.iti_item
    ).outerjoin(
        tables.ItemRelation,
        tables.ItemRelation.itr_child == tables.Item.itm_id
    ).outerjoin(
        item_alias,
        item_alias.itm_id == tables.ItemRelation.itr_parent
    )

    rows = query.all()

    # get choices of all questions included in the submissions to
    # compute max score of each question
    qst_ids = set(
        item.itm_id
        for _, item, _ in rows
        if item is not None and item.itm_type == types.ITEM_TYPE_QUESTION
    )
    query_questions = dbs.query(
        tables.Item,
        item_alias
    ).where(
        (tables.Item.itm_id.in_(qst_ids))
        & (tables.Item.itm_id == tables.ItemRelation.itr_parent)
        & (item_alias.itm_id == tables.ItemRelation.itr_child)
    )
    qst_choices: dict[tables.Item, set[tables.Item]] = dict()
    for qst, choice in query_questions:
        qst_choices.setdefault(qst, set()).add(choice)

    for sub, item, item_parent in rows:
        if sub.sub_id not in result:
            result[sub.sub_id] = {
                "sub": sub,
                "items": set(),
                "qst_answers": dict(),
                "qst_score": dict(),
                "qst_max_score": dict(),
                "cho_correct": dict()
            }
        result_sub = result[sub.sub_id]
        result_sub["items"].add(item)
        if item.itm_type == types.ITEM_TYPE_QUESTION:
            result_sub["qst_answers"].setdefault(item, set())
            result_sub["qst_score"].setdefault(item, 0)
            max_score = sum(1 for c in qst_choices[item] if c.itm_cho_correct)
            result_sub["qst_max_score"][item] = max_score
        elif item.itm_type == types.ITEM_TYPE_CHOICE:
            # itm_parent is the question of the choice
            assert item_parent is not None
            result_sub["qst_answers"].setdefault(item_parent, set())
            result_sub["qst_answers"][item_parent].add(item)
            result_sub["qst_score"].setdefault(item_parent, 0)
            if item.itm_cho_correct:
                result_sub["qst_score"][item_parent] += 1
                result_sub["cho_correct"][item] = True
            else:
                result_sub["qst_score"][item_parent] -= 1
                result_sub["cho_correct"][item] = False

    return result


def get_exam_result(dbs: Session, exm_id: int) -> exam_result_t:
    query = dbs.query(
        tables.Usr,
        tables.Registration,
        tables.Submission
    ).select_from(
        tables.Registration
    ).where(
        tables.Registration.reg_exam == exm_id
    ).join(
        tables.Usr,
        tables.Usr.usr_id == tables.Registration.reg_usr
    ).outerjoin(
        tables.Submission,
        tables.Submission.sub_exm_registration == tables.Registration.reg_id
    ).order_by(
        tables.Usr.usr_name,
        tables.Usr.usr_fst_name,
        tables.Usr.usr_code
    )
    rows = query.all()
    sub_ids = set(sub.sub_id for _, _, sub in rows if sub is not None)
    sub_results = get_submissions_result(dbs, sub_ids)
    for usr, reg, sub in rows:
        yield {
            "usr": usr,
            "reg": reg,
            "sub_result": sub_results[sub.sub_id] if sub is not None else None
        }


def get_exam(dbs: Session, exm_id: int) -> tables.Exam:
    result = dbs.query(tables.Exam).where(tables.Exam.exm_id == exm_id).first()
    assert result is not None
    return result


def get_submission(
        dbs: Session,
        sub_id: int
) -> tuple[tables.Submission, tables.Registration | None, tables.Exam | None]:
    result = dbs.query(
        tables.Submission,
        tables.Registration,
        tables.Exam
    ).select_from(
        tables.Submission
    ).where(
        tables.Submission.sub_id == sub_id
    ).outerjoin(
        tables.Registration,
        tables.Registration.reg_id == tables.Submission.sub_exm_registration
    ).outerjoin(
        tables.Exam,
        tables.Exam.exm_id == tables.Registration.reg_exam
    ).first()
    assert result is not None
    return result
