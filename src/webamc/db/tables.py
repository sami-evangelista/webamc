from sqlalchemy.orm import declarative_base

from webamc.all import *
from . import col_types as ct


FK = sa.ForeignKeyConstraint
UC = sa.UniqueConstraint
CC = sa.CheckConstraint
CO = sa.Column

Base = declarative_base()

now = sa.func.now()  # pylint: disable=not-callable


# definition of some foreign key column types
class RefUsr(ct.ForeignKey):
    pass
class RefAttr(ct.ForeignKey):
    pass
class RefTbl(ct.ForeignKey):
    pass
class RefSubmission(ct.ForeignKey):
    pass
class RefGrp(ct.ForeignKey):
    pass
class RefItem(ct.ForeignKey):
    pass
class RefItemInstance(ct.ForeignKey):
    pass
class RefTag(ct.ForeignKey):
    pass
class RefMcq(ct.ForeignKey):
    pass
class RefExam(ct.ForeignKey):
    pass
class RefRegistration(ct.ForeignKey):
    pass


# definition of some enumeration column types
class ItemDifficulty(ct.IntEnum):
    values = {
        t: str(t) for t in types.literal_type_values(types.item_difficulty_t)
    }
class ItemType(ct.IntEnum):
    values = {
        t: str(t) for t in types.literal_type_values(types.item_type_t)
    }
class McqMode(ct.IntEnum):
    values = {
        types.MCQ_MODE_EXAM: lang.txt("name_exam"),
        types.MCQ_MODE_REVIEW: lang.txt("name_review")
    }
class QstType(ct.IntEnum):
    values = {
        t: str(t) for t in types.literal_type_values(types.question_type_t)
    }
class TicketType(ct.IntEnum):
    values = {
        t: str(t) for t in types.literal_type_values(types.ticket_type_t)
    }
class UsrRight(ct.IntEnum):
    values = {
        types.USR_RIGHT_VIEW: lang.txt("name_view"),
        types.USR_RIGHT_SUBMIT: lang.txt("name_submission")
    }


class Usr(Base):
    __tablename__ = "usr"
    usr_id: int = CO(ct.Integer, primary_key=True)
    usr_code: str = CO(ct.String, nullable=False, unique=True)
    usr_eaddr: str = CO(ct.Eaddr, nullable=False, unique=True)
    usr_fst_name: str = CO(ct.FstName, nullable=False)
    usr_name: str = CO(ct.Name, nullable=False)


class Attr(Base):
    __tablename__ = "attr"
    atr_id: int = CO(ct.Integer, primary_key=True)
    atr_code: str = CO(ct.String, nullable=False, unique=True)
    atr_desc: str = CO(ct.String, nullable=False, unique=True)


class UsrAttr(Base):
    __tablename__ = "usr_attr"
    uat_id: int = CO(ct.Integer, primary_key=True)
    uat_usr: int = CO(RefUsr, nullable=False)
    uat_attr: int = CO(RefAttr, nullable=False)
    uat_value: str = CO(ct.String, nullable=False)
    __table_args__ = (
        UC("uat_usr", "uat_attr"),
        FK(["uat_usr"], ["usr.usr_id"], ondelete="CASCADE"),
        FK(["uat_attr"], ["attr.atr_id"], ondelete="CASCADE"),
    )


class Ticket(Base):
    __tablename__ = "ticket"
    tkt_id: int = CO(ct.Integer, primary_key=True)
    tkt_type: types.ticket_type_t = CO(TicketType, nullable=False)
    tkt_usr: None | int = CO(RefUsr)  # type: ignore
    tkt_eaddr: str = CO(ct.String, nullable=False)
    tkt_value: str = CO(ct.String, nullable=False)
    tkt_deadline: datetime.datetime = CO(ct.DateTime, nullable=False)
    __table_args__ = (
        FK(["tkt_usr"], ["usr.usr_id"], ondelete="CASCADE"),
        UC("tkt_type", "tkt_usr"),
        CC(f"tkt_type = {types.TICKET_ACCOUNT_CREATION} "
           "or tkt_usr is not null"),
    )


class CasAuth(Base):
    __tablename__ = "cas_auth"
    cas_id: int = CO(ct.Integer, primary_key=True)
    cas_enabled: bool = CO(ct.Boolean, nullable=False, default=False)
    cas_login: str = CO(ct.String, nullable=False, unique=True)
    cas_usr: int = CO(RefUsr, nullable=False, unique=True)
    __table_args__ = (
        FK(["cas_usr"], ["usr.usr_id"], ondelete="CASCADE"),
    )


class LocalAuth(Base):
    __tablename__ = "local_auth"
    loc_id: int = CO(ct.Integer, primary_key=True)
    loc_enabled: bool = CO(ct.Boolean, nullable=False, default=False)
    loc_login: str = CO(ct.String, nullable=False, unique=True)
    loc_password: str = CO(ct.Password)
    loc_usr: int = CO(RefUsr, nullable=False, unique=True)
    __table_args__ = (
        FK(["loc_usr"], ["usr.usr_id"], ondelete="CASCADE"),
    )


class Tbl(Base):
    __tablename__ = "tbl"
    tbl_id: int = CO(ct.Integer, primary_key=True)
    tbl_name: str = CO(ct.String, nullable=False, unique=True)


class Admin(Base):
    __tablename__ = "admin"
    adm_id: int = CO(ct.Integer, primary_key=True)
    adm_usr: int = CO(RefUsr, nullable=False)
    adm_tbl: int = CO(RefTbl, nullable=False)
    __table_args__ = (
        UC("adm_usr", "adm_tbl"),
        FK(["adm_usr"], ["usr.usr_id"], ondelete="CASCADE"),
        FK(["adm_tbl"], ["tbl.tbl_id"], ondelete="CASCADE"),
    )


class Item(Base):
    __tablename__ = "item"
    itm_id: int = CO(ct.Integer, primary_key=True)
    itm_type: types.item_type_t = CO(ItemType, nullable=False)
    itm_code = CO(ct.String)
    itm_title = CO(ct.String)
    itm_standalone: bool = CO(ct.Boolean, nullable=False, default=False)
    itm_rnd: bool = CO(ct.Boolean, nullable=False, default=False)
    itm_difficulty: None | types.item_difficulty_t = CO(  # type: ignore
        ItemDifficulty
    )
    itm_date: datetime.datetime = CO(
        ct.DateTime, nullable=False, server_default=now
    )
    itm_usr: int = CO(RefUsr, nullable=False)
    itm_visible: bool = CO(ct.Boolean, nullable=False, default=True)
    itm_parent: None | int = CO(RefItem)  # type: ignore
    itm_order = CO(ct.Integer)
    itm_img = CO(sa.LargeBinary)
    __table_args__ = (
        CC(ItemType.get_constraint("itm_type")),
        CC(ItemDifficulty.get_constraint("itm_difficulty")),
        CC(f"itm_code <> null or itm_type = {types.ITEM_TYPE_CHOICE}"),
        CC(f"itm_type <> {types.ITEM_TYPE_CHOICE} or itm_parent <> null"),
        FK(["itm_usr"], ["usr.usr_id"], ondelete="CASCADE"),
        FK(["itm_parent"], ["item.itm_id"], ondelete="CASCADE"),
        UC("itm_parent", "itm_order"),
        UC("itm_code", "itm_usr")
    )


class ItemInstance(Base):
    __tablename__ = "item_instance"
    iti_id: int = CO(ct.Integer, primary_key=True)
    iti_item: int = CO(RefItem, nullable=False)
    iti_num: int = CO(ct.Integer, nullable=False)
    iti_seed: int = CO(ct.Integer, nullable=False)
    iti_img = CO(sa.LargeBinary)
    __table_args__ = (
        UC("iti_item", "iti_num"),
        FK(["iti_item"], ["item.itm_id"], ondelete="CASCADE")
    )


class Mcq(Base):
    __tablename__ = "mcq"
    mcq_id: int = CO(RefItem, primary_key=True)
    mcq_mode: types.mcq_mode_t = CO(
        McqMode, nullable=False, default=types.MCQ_MODE_EXAM
    )
    __table_args__ = (
        FK(["mcq_id"], ["item.itm_id"], ondelete="CASCADE"),
    )


class Pack(Base):
    __tablename__ = "pack"
    pak_id: int = CO(RefItem, primary_key=True)
    pak_spec: str = CO(ct.String, nullable=False)
    __table_args__ = (
        FK(["pak_id"], ["item.itm_id"], ondelete="CASCADE"),
    )


class Question(Base):
    __tablename__ = "question"
    qst_id: int = CO(RefItem, primary_key=True)
    qst_type: types.question_type_t = CO(QstType, nullable=False)
    __table_args__ = (
        CC(QstType.get_constraint("qst_type")),
        FK(["qst_id"], ["item.itm_id"], ondelete="CASCADE")
    )


class Exercise(Base):
    __tablename__ = "exercise"
    exe_id: int = CO(RefItem, primary_key=True)
    __table_args__ = (
        FK(["exe_id"], ["item.itm_id"], ondelete="CASCADE"),
    )


class Choice(Base):
    __tablename__ = "choice"
    cho_id: int = CO(RefItem, primary_key=True)
    cho_correct: bool = CO(ct.Boolean, nullable=False)
    cho_last: bool = CO(ct.Boolean, nullable=False)
    __table_args__ = (
        FK(["cho_id"], ["item.itm_id"], ondelete="CASCADE"),
    )


class Tag(Base):
    __tablename__ = "tag"
    tag_id: int = CO(ct.Integer, primary_key=True)
    tag_name: str = CO(ct.String, nullable=False, unique=True)
    tag_desc: None | str = tp.cast(None | str, CO(ct.String))
    tag_color: None | str = tp.cast(None | str, CO(ct.Color))


class ItemTag(Base):
    __tablename__ = "item_tag"
    itg_id: int = CO(ct.Integer, primary_key=True)
    itg_item: int = CO(RefItem, nullable=False)
    itg_tag: int = CO(RefTag, nullable=False)
    __table_args__ = (
        UC("itg_item", "itg_tag"),
        FK(["itg_item"], ["item.itm_id"], ondelete="CASCADE"),
        FK(["itg_tag"], ["tag.tag_id"], ondelete="CASCADE")
    )


class Registration(Base):
    __tablename__ = "registration"
    reg_id: int = CO(ct.Integer, primary_key=True)
    reg_usr: int = CO(RefUsr, nullable=False)
    reg_exam: int = CO(RefExam, nullable=False)
    reg_date: datetime.datetime = CO(
        ct.DateTime, nullable=False, server_default=now
    )
    __table_args__ = (
        UC("reg_usr", "reg_exam"),
        FK(["reg_usr"], ["usr.usr_id"], ondelete="CASCADE"),
        FK(["reg_exam"], ["exam.exm_id"], ondelete="CASCADE"),
    )


class Submission(Base):
    __tablename__ = "submission"
    sub_id: int = CO(ct.Integer, primary_key=True)
    sub_date: datetime.datetime = CO(ct.DateTime, nullable=False)


class ExamSubmission(Base):
    __tablename__ = "exam_submission"
    exs_id: int = CO(RefSubmission, primary_key=True)
    exs_content: str = CO(ct.String, nullable=False)
    exs_registration: int = CO(RefRegistration, nullable=False)
    exs_date_update: datetime.datetime = CO(ct.DateTime, nullable=False)
    __table_args__ = (
        FK(["exs_id"], ["submission.sub_id"], ondelete="CASCADE"),
        FK(["exs_registration"], ["registration.reg_id"], ondelete="CASCADE"),
    )


class ReviewSubmission(Base):
    __tablename__ = "review_submission"
    rvs_id: int = CO(RefSubmission, primary_key=True)
    rvs_usr: int = CO(RefUsr, nullable=False)
    rvs_mcq: int = CO(RefItem, nullable=False)
    __table_args__ = (
        FK(["rvs_id"], ["submission.sub_id"], ondelete="CASCADE"),
        FK(["rvs_usr"], ["usr.usr_id"], ondelete="CASCADE"),
        FK(["rvs_mcq"], ["item.itm_id"], ondelete="CASCADE"),
    )


class Answer(Base):
    __tablename__ = "answer"
    ans_id: int = CO(ct.Integer, primary_key=True)
    ans_submission: int = CO(RefSubmission, nullable=False)
    ans_instance: int = CO(RefItemInstance, nullable=False)
    __table_args__ = (
        UC("ans_submission", "ans_instance"),
        FK(["ans_submission"], ["submission.sub_id"], ondelete="CASCADE"),
        FK(["ans_instance"], ["item_instance.iti_id"], ondelete="CASCADE")
    )


class Grp(Base):
    __tablename__ = "grp"
    grp_id: int = CO(ct.Integer, primary_key=True)
    grp_name: str = CO(ct.String, nullable=False, unique=True)
    grp_parent: int = CO(RefGrp)
    __table_args__ = (
        FK(["grp_parent"], ["grp.grp_id"], ondelete="CASCADE"),
        CC("grp_parent IS NULL OR grp_parent <> grp_id"),
    )


class Exam(Base):
    __tablename__ = "exam"
    exm_id: int = CO(ct.Integer, primary_key=True)
    exm_mcq: int = CO(RefMcq, nullable=False)
    exm_start: datetime.datetime = CO(ct.DateTime, nullable=False)
    exm_duration: int = CO(ct.PositiveInteger, nullable=False, default=60)
    __table_args__ = (
        FK(["exm_mcq"], ["mcq.mcq_id"], ondelete="CASCADE"),
        CC("exm_duration > 0"),
    )
    @staticmethod
    def end_time(exam: "Exam") -> datetime.datetime:
        return exam.exm_start + datetime.timedelta(minutes=exam.exm_duration)


class UsrGrp(Base):
    __tablename__ = "usr_grp"
    ugp_id = CO(ct.Integer, primary_key=True)
    ugp_usr: int = CO(RefUsr, nullable=False)
    ugp_grp: int = CO(RefGrp, nullable=False)
    ugp_right: types.usr_right_t = CO(UsrRight, nullable=False)
    __table_args__ = (
        UC("ugp_usr", "ugp_grp", "ugp_right"),
        CC(UsrRight.get_constraint("ugp_right")),
        FK(["ugp_usr"], ["usr.usr_id"], ondelete="CASCADE"),
        FK(["ugp_grp"], ["grp.grp_id"], ondelete="CASCADE"),
    )


class McqGrp(Base):
    __tablename__ = "mcq_grp"
    mgp_id: int = CO(ct.Integer, primary_key=True)
    mgp_mcq: int = CO(RefMcq, nullable=False)
    mgp_grp: int = CO(RefGrp, nullable=False)
    __table_args__ = (
        UC("mgp_mcq", "mgp_grp"),
        FK(["mgp_grp"], ["grp.grp_id"], ondelete="CASCADE"),
        FK(["mgp_mcq"], ["mcq.mcq_id"], ondelete="CASCADE"),
    )


TBL_CODES: dict[str, list[str]] = {
    "admin": ["adm_usr", "adm_tbl"],
    "attr": ["atr_code"],
    "local_auth": ["loc_login"],
    "cas_auth": ["cas_login"],
    "grp": ["grp_name"],
    "tag": ["tag_name"],
    "tbl": ["tbl_name"],
    "usr": ["usr_code"],
    "usr_attr": ["uat_usr", "uat_attr"],
    "usr_grp": ["ugp_usr", "ugp_grp", "ugp_right"],
    "review_submission": ["rvs_usr", "rvs_mcq"]
}


# define attributes of foreign keys
RefUsr.col = Usr.usr_id
RefUsr.fmt = lambda usr: str(usr.usr_code)
RefAttr.col = Attr.atr_id
RefAttr.fmt = lambda attr: str(attr.atr_code)
RefTbl.col = Tbl.tbl_id
RefTbl.fmt = lambda tbl: str(tbl.tbl_name)
RefSubmission.col = Submission.sub_id
RefSubmission.fmt = lambda sub: str(sub.sub_id)
RefGrp.col = Grp.grp_id
RefGrp.fmt = lambda grp: str(grp.grp_name)
RefItem.col = Item.itm_id
RefItem.fmt = lambda item: str(item.itm_code)
RefTag.col = Tag.tag_id
RefTag.fmt = lambda tag: str(tag.tag_name)
RefMcq.col = Mcq.mcq_id
RefMcq.fmt = lambda mcq: str(mcq.mcq_id)
RefExam.col = Exam.exm_id
RefExam.fmt = lambda exam: str(exam.exm_id)
RefRegistration.col = Registration.reg_id
RefRegistration.fmt = lambda reg: str(reg.reg_id)

RefItemInstance.col = ItemInstance.iti_id
RefItemInstance.fmt = lambda iti: str(iti.iti_id)
