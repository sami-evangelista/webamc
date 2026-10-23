import datetime
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


def get_exam_monitoring(
        dbs: Session,
        exm_id: int
) -> types.exam_monitoring_t | None:

    # get exam info
    exam = dbs.query(
        tables.Exam
    ).where(
        tables.Exam.exm_id == exm_id
    ).first()
    if not exam:
        return None

    # count the number of questions each registered user answered
    query_answers = dbs.query(
        tables.Registration.reg_usr,
        tables.ItemRelation.itr_parent
    ).select_from(
        tables.Registration
    ).where(
        tables.Registration.reg_exam == exm_id
    ).join(
        tables.Submission,
        tables.Submission.sub_exm_registration == tables.Registration.reg_id
    ).join(
        tables.Answer,
        tables.Answer.ans_submission == tables.Submission.sub_id
    ).join(
        tables.ItemInstance,
        tables.ItemInstance.iti_id == tables.Answer.ans_instance
    ).join(
        tables.Item,
        tables.Item.itm_id == tables.ItemInstance.iti_item
    ).where(
        tables.Item.itm_type == types.ITEM_TYPE_CHOICE
    ).join(
        tables.ItemRelation,
        tables.ItemRelation.itr_child == tables.Item.itm_id
    )
    answered_count: dict[int, set[int]] = dict()
    for row_answer in query_answers.all():
        usr_id, itm_id = row_answer._tuple()
        answered_count.setdefault(usr_id, set()).add(itm_id)

    # list (usr, registration, submission) for this exam. submission
    # may be None if the user has not started the exam.
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
        tables.Registration.reg_id == tables.Submission.sub_exm_registration
    ).order_by(
        tables.Usr.usr_name,
        tables.Usr.usr_fst_name
    )

    now = datetime.datetime.now()
    students_data: list[types.student_monitoring_t] = []
    for row in query.all():
        usr, reg, sub = row._tuple()
        student_status: types.exam_student_status_t = "not-started"
        last_seen: datetime.datetime | None = None
        score = 0.0
        total_questions = 0
        if sub is not None:
            assert sub.sub_exm_date_update is not None
            assert sub.sub_exm_content is not None
            last_seen = sub.sub_exm_date_update
            content = tp.cast(
                types.mcq_content_t,
                json.loads(sub.sub_exm_content)
            )
            student_status = "online"
            if now - last_seen > datetime.timedelta(minutes=5):
                student_status = "inactive"
            total_questions = sum(
                1 for c, _ in types.mcq_enum_items(content)
                if c["itm_type"] == types.ITEM_TYPE_QUESTION
            )
            #detailed_scores = get_student_detailed_scores(
            #    dbs, exam.exm_mcq, sub.exs_id
            #)
            #score = sum(detailed_scores.values())
            score = 0

        if usr.usr_id not in answered_count:
            count = 0
        else:
            count = len(answered_count[usr.usr_id])
        students_data.append({
            "reg_id": int(reg.reg_id),
            "usr_name": str(usr.usr_name),
            "usr_fst_name": str(usr.usr_fst_name),
            "status": student_status,
            "last_seen": last_seen,
            "answered_count": count,
            "total_questions": total_questions,
            "score": score
        })

    # exam status
    exam_status: types.exam_status_t
    if now < exam.exm_start:
        exam_status = "upcoming"
    elif now > exam.end_time():
        exam_status = "finished"
    else:
        exam_status = "in-progress"

    return {
        "status": exam_status,
        "start": exam.exm_start,
        "end": exam.end_time(),
        "students": students_data
    }


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
        if oper == "by-difficulty":
            return result.where(
                tables.Item.itm_difficulty.in_(arg) if not rev
                else tables.Item.itm_difficulty.not_in(arg)
            )
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


def get_img(dbs: Session, itm_id: int, iti_num: int = 1) -> bytes | None:
    instance = dbs.query(
        tables.ItemInstance
    ).where(
        (tables.ItemInstance.iti_item == itm_id)
        & (tables.ItemInstance.iti_num == iti_num)
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

def get_exam_questions(dbs: Session, mcq_id: int) -> list[tables.Item]:
    return list()
"""
    direct_items = dbs.query(tables.Item.itm_id).filter(
        tables.Item.itm_parent == mcq_id
    ).all()
    parent_ids = [mcq_id] + [item.itm_id for item in direct_items]
    result = dbs.query(tables.Question).join(
        tables.Item, tables.Question.qst_id == tables.Item.itm_id
    ).filter(
        tables.Item.itm_parent.in_(parent_ids)
    ).all()
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
