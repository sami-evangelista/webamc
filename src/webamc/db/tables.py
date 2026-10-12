from sqlalchemy.orm import declarative_base
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.engine.base import Connection
from sqlalchemy import ForeignKeyConstraint, CheckConstraint, UniqueConstraint

from webamc.all import *
from . import col_types as ct, errors

Base = declarative_base()

now = sa.func.now()


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
    usr_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    usr_code: str = sa.Column(
        ct.String,
        nullable=False,
        unique=True,
        doc=r"unique user code",
    )
    usr_eaddr: str = sa.Column(
        ct.Eaddr,
        nullable=False,
        unique=True,
        doc=r"unique electronic address"
    )
    usr_fst_name: str = sa.Column(
        ct.FstName,
        nullable=False,
        doc=r"first name"
    )
    usr_name: str = sa.Column(
        ct.Name,
        nullable=False,
        doc=r"last name"
    )
    __code__ = usr_code
    __doc__ = "This table defines users."


class Attr(Base):
    __tablename__ = "attr"
    atr_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    atr_code: str = sa.Column(
        ct.String,
        nullable=False,
        unique=True,
        doc=r"unique attribute code"
    )
    atr_desc: str = sa.Column(
        ct.String,
        nullable=False,
        unique=True,
        doc=r"a description of the attribute"
    )
    __code__ = atr_code
    __doc__ = """This table lists attributes that may be associated to
       users (e.g., student ID)."""


class UsrAttr(Base):
    __tablename__ = "usr_attr"
    uat_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    uat_usr: int = sa.Column(
        RefUsr,
        nullable=False,
        doc=r"user (references {\tt usr.usr\_code})"
    )
    uat_attr: int = sa.Column(
        RefAttr,
        nullable=False,
        doc=r"attribute (references {\tt attr.atr\_code})"
    )
    uat_value: str = sa.Column(
        ct.String,
        nullable=False,
        doc="value of the attribute for the user"
    )
    __table_args__ = (
        UniqueConstraint(
            "uat_usr",
            "uat_attr"
        ),
        ForeignKeyConstraint(
            ["uat_usr"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["uat_attr"],
            ["attr.atr_id"],
            ondelete="CASCADE"
        ),
    )
    __doc__ = "This table associates users and attributes."


class Ticket(Base):
    __tablename__ = "ticket"
    tkt_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    tkt_type: types.ticket_type_t = sa.Column(
        TicketType,
        nullable=False
    )
    tkt_usr: int | None = sa.Column(  # type: ignore
        RefUsr
    )
    tkt_eaddr: str = sa.Column(
        ct.String,
        nullable=False
    )
    tkt_value: str = sa.Column(
        ct.String,
        nullable=False
    )
    tkt_deadline: datetime.datetime = sa.Column(
        ct.DateTime,
        nullable=False
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["tkt_usr"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
        UniqueConstraint(
            "tkt_type",
            "tkt_usr"
        ),
        CheckConstraint(
            f"tkt_type = {types.TICKET_ACCOUNT_CREATION} "
            "or tkt_usr is not null"
        ),
    )


class CasAuth(Base):
    __tablename__ = "cas_auth"
    cas_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    cas_enabled: bool = sa.Column(
        ct.Boolean,
        default=False,
        nullable=False,
        doc="1 if CAS authentication enabled for the user, 0 otherwise"
    )
    cas_login: str = sa.Column(
        ct.String,
        nullable=False,
        unique=True,
        doc="login of the user on the CAS server"
    )
    cas_usr: int = sa.Column(
        RefUsr,
        nullable=False,
        unique=True,
        doc=r"user which is granted access (references {\tt usr.usr\_code})"
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["cas_usr"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
    )
    __code__ = cas_login
    __doc__ = """This table controls CAS authentication. Each row
       gives access to one user."""


class LocalAuth(Base):
    __tablename__ = "local_auth"
    loc_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    loc_enabled: bool = sa.Column(
        ct.Boolean,
        nullable=False,
        default=False,
        doc=r"1 if local authentication is enabled for the user, 0 otherwise"
    )
    loc_login: str = sa.Column(
        ct.String,
        nullable=False,
        unique=True,
        doc=r"login of the user"
    )
    loc_password: str = sa.Column(
        ct.Password,
        doc="plain-text password (possibly empty)"
    )
    loc_usr: int = sa.Column(
        RefUsr,
        nullable=False,
        unique=True,
        doc=r"user which is granted access (references {\tt usr.usr\_code})"
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["loc_usr"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
    )
    __code__ = loc_login
    __doc__ = r"""This table controls local system
       authentication. Each row gives access to one user. The login
       used by the user to authenticate is her/his code. An empty
       password prevents the user from logging meaning that he/she has
       to first reset his/her password. If not empty, the password is
       given plain."""


class Tbl(Base):
    __tablename__ = "tbl"
    tbl_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    tbl_name: str = sa.Column(
        ct.String,
        nullable=False,
        unique=True,
        doc=r"unique table name"
    )
    __code__ = tbl_name
    __doc__ = """This table contains the list of names of tables which
       can be administrated through the web interface, i.e., for which
       CSV file submission is allowed."""


class Admin(Base):
    __tablename__ = "admin"
    adm_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    adm_usr: int = sa.Column(
        RefUsr,
        nullable=False,
        doc=r"""user which is granted admin right (references {\tt
           usr.usr\_code})"""
    )
    adm_tbl: int = sa.Column(
        RefTbl,
        nullable=False,
        doc=r"""table on which this right admin right is granted
           (references {\tt tbl.tbl\_name})"""
    )
    __table_args__ = (
        UniqueConstraint(
            "adm_usr",
            "adm_tbl"
        ),
        ForeignKeyConstraint(
            ["adm_usr"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["adm_tbl"],
            ["tbl.tbl_id"],
            ondelete="CASCADE"
        ),
    )
    __doc__ = """This table defines grants administration privileges
       to users on tables."""


class Item(Base):
    __tablename__ = "item"
    itm_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    itm_type: types.item_type_t = sa.Column(
        ItemType,
        nullable=False
    )
    itm_code: str | None = sa.Column(  # type: ignore
        ct.ItemCode
    )
    itm_title: str | None = sa.Column(  # type: ignore
        ct.String
    )
    itm_is_mcq: bool = sa.Column(
        ct.Boolean,
        nullable=False
    )
    itm_standalone: bool = sa.Column(
        ct.Boolean,
        nullable=False,
        default=False
    )
    itm_rnd: bool = sa.Column(
        ct.Boolean,
        nullable=False,
        default=False
    )
    itm_difficulty: int | None = sa.Column(  # type: ignore
        ItemDifficulty
    )
    itm_date: datetime.datetime = sa.Column(
        ct.DateTime,
        nullable=False,
        server_default=now
    )
    itm_usr: int = sa.Column(
        RefUsr,
        nullable=False
    )
    itm_visible: bool = sa.Column(
        ct.Boolean,
        nullable=False,
        default=True
    )
    itm_parent: int | None = sa.Column(  # type: ignore
        RefItem
    )
    __table_args__ = (
        CheckConstraint(
            ItemType.get_constraint("itm_type")
        ),
        CheckConstraint(
            ItemDifficulty.get_constraint("itm_difficulty")
        ),
        CheckConstraint(
            f"not itm_is_mcq or itm_type = {types.ITEM_TYPE_EXERCISE} "
            f"or itm_type = {types.ITEM_TYPE_PACK}"
        ),
        CheckConstraint(
            f"itm_code is not null or itm_type = {types.ITEM_TYPE_CHOICE}"
        ),
        CheckConstraint(
            f"itm_parent is not null or itm_type <> {types.ITEM_TYPE_CHOICE}"
        ),
        CheckConstraint(
            f"itm_parent is null or itm_type = {types.ITEM_TYPE_CHOICE}"
        ),
        ForeignKeyConstraint(
            ["itm_usr"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["itm_parent"],
            ["item.itm_id"],
            ondelete="CASCADE"
        ),
        UniqueConstraint(
            "itm_code",
            "itm_usr"
        )
    )


class ItemRelation(Base):
    __tablename__ = "item_relation"
    itr_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    itr_parent: int = sa.Column(
        RefItem,
        nullable=False
    )
    itr_child: int = sa.Column(
        RefItem,
        nullable=False
    )
    itr_order: int = sa.Column(
        ct.Integer,
        nullable=False
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["itr_parent"],
            ["item.itm_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["itr_child"],
            ["item.itm_id"],
            ondelete="CASCADE"
        ),
        UniqueConstraint(
            "itr_parent",
            "itr_order"
        ),
    )



class ItemInstance(Base):
    __tablename__ = "item_instance"
    iti_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    iti_item: int = sa.Column(
        RefItem,
        nullable=False
    )
    iti_num: int = sa.Column(
        ct.Integer,
        nullable=False
    )
    iti_seed: int = sa.Column(
        ct.Integer,
        nullable=False
    )
    iti_img: bytes | None = sa.Column(  # type: ignore
        sa.LargeBinary
    )
    __table_args__ = (
        UniqueConstraint(
            "iti_item",
            "iti_num"
        ),
        ForeignKeyConstraint(
            ["iti_item"],
            ["item.itm_id"],
            ondelete="CASCADE"
        )
    )


class Mcq(Base):
    __tablename__ = "mcq"
    mcq_id: int = sa.Column(
        RefItem,
        primary_key=True
    )
    mcq_mode: types.mcq_mode_t = sa.Column(
        McqMode,
        nullable=False,
        default=types.MCQ_MODE_EXAM
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["mcq_id"],
            ["item.itm_id"],
            ondelete="CASCADE"
        ),
    )


class Pack(Base):
    __tablename__ = "pack"
    pak_id: int = sa.Column(
        RefItem,
        primary_key=True
    )
    pak_spec: str = sa.Column(
        ct.PackSpec,
        nullable=False
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["pak_id"],
            ["item.itm_id"],
            ondelete="CASCADE"
        ),
    )


class Question(Base):
    __tablename__ = "question"
    qst_id: int = sa.Column(
        RefItem,
        primary_key=True
    )
    qst_type: types.question_type_t = sa.Column(
        QstType,
        nullable=False
    )
    __table_args__ = (
        CheckConstraint(
            QstType.get_constraint("qst_type")
        ),
        ForeignKeyConstraint(
            ["qst_id"],
            ["item.itm_id"],
            ondelete="CASCADE"
        )
    )


class Exercise(Base):
    __tablename__ = "exercise"
    exe_id: int = sa.Column(
        RefItem,
        primary_key=True
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["exe_id"],
            ["item.itm_id"],
            ondelete="CASCADE"
        ),
    )


class Choice(Base):
    __tablename__ = "choice"
    cho_id: int = sa.Column(
        RefItem,
        primary_key=True
    )
    cho_correct: bool = sa.Column(
        ct.Boolean,
        nullable=False
    )
    cho_last: bool = sa.Column(
        ct.Boolean,
        nullable=False
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["cho_id"],
            ["item.itm_id"],
            ondelete="CASCADE"
        ),
    )


class Tag(Base):
    __tablename__ = "tag"
    tag_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    tag_name: str = sa.Column(
        ct.String,
        nullable=False,
        unique=True,
        doc="unique tag name"
    )
    tag_desc: str | None = sa.Column(  # type: ignore
        ct.String,
        doc="tag description (possibly empty)"
    )
    tag_color: str | None = sa.Column(  # type: ignore
        ct.Color,
        doc=r"tag color of the form \verb+#RRGGBB+ (possibly empty)"
    )
    __code__ = tag_name
    __doc__ = """This table defines tags that can be associated to MCQ
       items (e.g., questions)."""


class ItemTag(Base):
    __tablename__ = "item_tag"
    itg_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    itg_item: int = sa.Column(
        RefItem,
        nullable=False
    )
    itg_tag: int = sa.Column(
        RefTag,
        nullable=False
    )
    __table_args__ = (
        UniqueConstraint(
            "itg_item",
            "itg_tag"
        ),
        ForeignKeyConstraint(
            ["itg_item"],
            ["item.itm_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["itg_tag"],
            ["tag.tag_id"],
            ondelete="CASCADE"
        )
    )


class Registration(Base):
    __tablename__ = "registration"
    reg_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    reg_usr: int = sa.Column(
        RefUsr,
        nullable=False
    )
    reg_exam: int = sa.Column(
        RefExam,
        nullable=False
    )
    reg_date: datetime.datetime = sa.Column(
        ct.DateTime,
        nullable=False,
        server_default=now
    )
    __table_args__ = (
        UniqueConstraint(
            "reg_usr",
            "reg_exam"
        ),
        ForeignKeyConstraint(
            ["reg_usr"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["reg_exam"],
            ["exam.exm_id"],
            ondelete="CASCADE"
        ),
    )


class Submission(Base):
    __tablename__ = "submission"
    sub_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    sub_date: datetime.datetime = sa.Column(
        ct.DateTime,
        nullable=False
    )


class ExamSubmission(Base):
    __tablename__ = "exam_submission"
    exs_id: int = sa.Column(
        RefSubmission,
        primary_key=True
    )
    exs_content: str = sa.Column(
        ct.String,
        nullable=False
    )
    exs_registration: int = sa.Column(
        RefRegistration,
        nullable=False
    )
    exs_date_update: datetime.datetime = sa.Column(
        ct.DateTime,
        nullable=False
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["exs_id"],
            ["submission.sub_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["exs_registration"],
            ["registration.reg_id"],
            ondelete="CASCADE"
        ),
    )


class ReviewSubmission(Base):
    __tablename__ = "review_submission"
    rvs_id: int = sa.Column(
        RefSubmission,
        primary_key=True
    )
    rvs_usr: int = sa.Column(
        RefUsr,
        nullable=False
    )
    rvs_mcq: int = sa.Column(
        RefItem,
        nullable=False
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["rvs_id"],
            ["submission.sub_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["rvs_usr"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["rvs_mcq"],
            ["item.itm_id"],
            ondelete="CASCADE"
        ),
    )


class Answer(Base):
    __tablename__ = "answer"
    ans_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    ans_submission: int = sa.Column(
        RefSubmission,
        nullable=False
    )
    ans_instance: int = sa.Column(
        RefItemInstance,
        nullable=False
    )
    __table_args__ = (
        UniqueConstraint(
            "ans_submission",
            "ans_instance"
        ),
        ForeignKeyConstraint(
            ["ans_submission"],
            ["submission.sub_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["ans_instance"],
            ["item_instance.iti_id"],
            ondelete="CASCADE"
        )
    )


class Grp(Base):
    __tablename__ = "grp"
    grp_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    grp_name: str = sa.Column(
        ct.String,
        nullable=False,
        unique=True,
        doc="unique group name"
    )
    grp_parent: int | None = sa.Column(  # type: ignore
        RefGrp,
        doc=r"""parent group name (possibly empty, references {\tt
           grp.grp\_name})"""
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["grp_parent"],
            ["grp.grp_id"],
            ondelete="CASCADE"
        ),
        CheckConstraint(
            "grp_parent IS NULL OR grp_parent <> grp_id"
        ),
    )
    __code__ = grp_name
    __doc__ = "This table defines user groups."


class Exam(Base):
    __tablename__ = "exam"
    exm_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    exm_mcq: int = sa.Column(
        RefMcq,
        nullable=False
    )
    exm_start: datetime.datetime = sa.Column(
        ct.DateTime,
        nullable=False
    )
    exm_duration: int = sa.Column(
        ct.PositiveInteger,
        nullable=False,
        default=60
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["exm_mcq"],
            ["mcq.mcq_id"],
            ondelete="CASCADE"
        ),
        CheckConstraint(
            "exm_duration > 0"
        ),
    )
    @staticmethod
    def end_time(exam: "Exam") -> datetime.datetime:
        return exam.exm_start + datetime.timedelta(minutes=exam.exm_duration)


class UsrGrp(Base):
    __tablename__ = "usr_grp"
    ugp_id = sa.Column(
        ct.Integer,
        primary_key=True
    )
    ugp_usr: int = sa.Column(
        RefUsr,
        nullable=False,
        doc=r"user (references {\tt usr.usr\_code})"
    )
    ugp_grp: int = sa.Column(
        RefGrp,
        nullable=False,
        doc=r"group (references {\tt grp.grp\_name})"
    )
    ugp_right: types.usr_right_t = sa.Column(
        UsrRight,
        nullable=False,
        doc=fr"""right given to the user on the group:
           {types.USR_RIGHT_VIEW} for view (right to view MCQ
           submitted for that group), {types.USR_RIGHT_SUBMIT} for
           submit (right to submit MCQ for that group)"""
    )
    __table_args__ = (
        UniqueConstraint(
            "ugp_usr",
            "ugp_grp",
            "ugp_right"
        ),
        CheckConstraint(
            UsrRight.get_constraint("ugp_right")
        ),
        ForeignKeyConstraint(
            ["ugp_usr"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["ugp_grp"],
            ["grp.grp_id"],
            ondelete="CASCADE"
        ),
    )
    __doc__ = "This table defines group memberships."


class McqGrp(Base):
    __tablename__ = "mcq_grp"
    mgp_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    mgp_mcq: int = sa.Column(
        RefMcq,
        nullable=False
    )
    mgp_grp: int = sa.Column(
        RefGrp,
        nullable=False
    )
    __table_args__ = (
        UniqueConstraint(
            "mgp_mcq",
            "mgp_grp"
        ),
        ForeignKeyConstraint(
            ["mgp_grp"],
            ["grp.grp_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["mgp_mcq"],
            ["mcq.mcq_id"],
            ondelete="CASCADE"
        ),
    )


class Message(Base):
    __tablename__ = "message"
    msg_id: int = sa.Column(
        ct.Integer,
        primary_key=True
    )
    msg_title: str = sa.Column(
        ct.String,
        nullable=False
    )
    msg_code: str = sa.Column(
        ct.String,
        nullable=False
    )
    msg_date: datetime.datetime = sa.Column(
        ct.DateTime,
        nullable=False,
        server_default=now
    )
    msg_from: int = sa.Column(
        RefUsr,
        nullable=False
    )
    msg_to: int = sa.Column(
        RefUsr,
        nullable=False
    )
    msg_file: bytes = sa.Column(
        sa.LargeBinary,
        nullable=False
    )
    msg_filename: str = sa.Column(
        ct.String,
        nullable=False
    )
    __table_args__ = (
        UniqueConstraint(
            "msg_from",
            "msg_to",
            "msg_code"
        ),
        ForeignKeyConstraint(
            ["msg_from"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["msg_to"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
    )


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


def create_listeners() -> tp.Any:

    # checks performed during or insert or update
    def basic_checks(
            tbl: sa.sql.schema.Table,
            conn: Connection,
            target: tp.Any,
            row_id: None | int
    ) -> None:
        tname = tbl.name
        pkey = next(c for c in tbl.columns if c.primary_key)
        for col in tbl.columns:
            cname = col.name
            val = getattr(target, cname, None)
            null_val = val is None or val == ""

            # check non null values
            if isinstance(col.type, ct.ColType) and not null_val:
                try:
                    val = col.type.val_chk(val, conn=conn)
                    val = col.type.val_transform(val)
                    setattr(target, cname, val)
                except ValueError as ex:
                    raise errors.DBInvalidValue(tname, cname, val) from ex

            # check uniqueness (single column)
            if col.unique:
                cond = col == val
                if row_id is not None:
                    cond = cond & (pkey != row_id)
                row = conn.execute(tbl.select().where(cond)).first()
                if row is not None:
                    raise errors.DBDuplicateValue(tname, cname, val)

        # check uniqueness constraints of the table
        for cons in tbl.constraints:
            if (
                    isinstance(cons, UniqueConstraint)
                    and all(
                        getattr(target, col.name, None) is not None
                        for col in cons.columns
                    )
            ):
                cond = sa.and_(
                    *(col == getattr(target, col.name) for col in cons.columns)
                )
                if row_id is not None:
                    cond = cond & (pkey != row_id)
                row = conn.execute(tbl.select().where(cond)).first()
                if row is not None:
                    raise errors.DBDuplicateValue(
                        tbl.name,
                        [col.name for col in cons.columns],
                        [getattr(target, col.name) for col in cons.columns]
                    )

    def insert_listener(t):  # type: ignore
        def result(
                mapper: Mapper[tp.Any],
                conn: Connection,
                target: tp.Any
        ) -> None:
            tbl: sa.sql.schema.Table = t.__table__
            tname = tbl.name
            basic_checks(tbl, conn, target, None)

            # check null values are allowed
            for col in tbl.columns:
                cname = col.name
                val = getattr(target, cname, None)
                null_val = val is None or val == ""
                if (
                        null_val
                        and not col.nullable
                        and not col.primary_key
                ):
                    raise errors.DBInvalidNullValue(tname, cname)

        return result
    def update_listener(t):  # type: ignore
        def result(
                mapper: Mapper[tp.Any],
                conn: Connection,
                target: tp.Any
        ) -> None:
            tbl: sa.sql.schema.Table = t.__table__
            tname = tbl.name
            pkey = next(c for c in tbl.columns if c.primary_key)
            basic_checks(tbl, conn, target, getattr(target, pkey.name))

            # check null values are allowed
            for col in tbl.columns:
                cname = col.name
                if (
                        hasattr(target, cname)
                        and getattr(target, cname) is None
                        and not col.nullable
                ):
                    raise errors.DBInvalidNullValue(tname, cname)
        return result
    t: tp.Any
    for t in Base.__subclasses__():
        sa.event.listen(t, "before_insert", insert_listener(t))  # type: ignore
        sa.event.listen(t, "before_update", update_listener(t))  # type: ignore


create_listeners()
