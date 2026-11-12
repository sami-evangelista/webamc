import uuid
from pathlib import Path
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.orm.mapper import Mapper
from sqlalchemy.engine.base import Connection
from sqlalchemy import (
    select, delete, ForeignKeyConstraint, CheckConstraint, UniqueConstraint
)

from webamc.all import *
from . import col_types as ct, errors


now = sa.func.now()


def implies(left: str, right: str) -> CheckConstraint:
    return CheckConstraint(f"not ({left}) or ({right})")


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
class RefExam(ct.ForeignKey):
    pass
class RefRegistration(ct.ForeignKey):
    pass
class RefProject(ct.ForeignKey):
    pass


# definition of some enumeration column types
class ItemType(ct.IntEnum):
    values = {
        t: str(t) for t in types.literal_type_values(types.item_type_t)
    }
class McqMode(ct.IntEnum):
    values = {
        types.MCQ_MODE_EXAM: lang.txt("base_exam"),
        types.MCQ_MODE_REVIEW: lang.txt("base_review")
    }
class QstType(ct.IntEnum):
    values = {
        types.QUESTION_TYPE_SINGLE: lang.txt("seq_qst_type_single"),
        types.QUESTION_TYPE_MULTI: lang.txt("seq_qst_type_multi")
    }
class TicketType(ct.IntEnum):
    values = {
        t: str(t) for t in types.literal_type_values(types.ticket_type_t)
    }
class UsrRight(ct.IntEnum):
    values = {
        types.USR_RIGHT_VIEW: lang.txt("base_view"),
        types.USR_RIGHT_SUBMIT: lang.txt("base_submission")
    }
class SubmissionType(ct.IntEnum):
    values = {
        t: str(t) for t in types.literal_type_values(types.submission_type_t)
    }
class MessageType(ct.IntEnum):
    values = {
        t: str(t) for t in types.literal_type_values(types.message_type_t)
    }


class Base(DeclarativeBase):
    pass


class Usr(Base):
    __tablename__ = "usr"
    info = {
        "code": "usr_code",
        "doc": "This table defines users."
    }
    usr_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True,
        info={
            "ui_visible": True
        }
    )
    usr_code: Mapped[str] = mapped_column(
        ct.String,
        nullable=False,
        unique=True,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"unique user code",
        }
    )
    usr_eaddr: Mapped[str] = mapped_column(
        ct.Eaddr,
        nullable=False,
        unique=True,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"unique electronic address"
        }
    )
    usr_fst_name: Mapped[str] = mapped_column(
        ct.FstName,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"first name"
        }
    )
    usr_name: Mapped[str] = mapped_column(
        ct.Name,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"last name"
        }
    )
    def fmt(self) -> str:
        result = f"{self.usr_name.upper()} {self.usr_fst_name.title()}"
        result += f" [{self.usr_code}]"
        return result


class Attr(Base):
    __tablename__ = "attr"
    info = {
        "code": "atr_code",
        "doc": """This table lists attributes that may be associated to
           users (e.g., student ID)."""
    }
    atr_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True,
        info={
            "ui_visible": True
        }
    )
    atr_code: Mapped[str] = mapped_column(
        ct.String,
        nullable=False,
        unique=True,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"unique attribute code"
        }
    )
    atr_desc: Mapped[str] = mapped_column(
        ct.String,
        nullable=False,
        unique=True,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"a description of the attribute",
        }
    )


class UsrAttr(Base):
    __tablename__ = "usr_attr"
    info = {
        "doc": "This table associates users and attributes."
    }
    uat_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True,
        info={
            "ui_visible": True
        }
    )
    uat_usr: Mapped[int] = mapped_column(
        RefUsr,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"user (references {\tt usr.usr\_code})"
        }
    )
    uat_attr: Mapped[int] = mapped_column(
        RefAttr,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"attribute (references {\tt attr.atr\_code})"
        }
    )
    uat_value: Mapped[str] = mapped_column(
        ct.String,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": "value of the attribute for the user"
        }
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


class Ticket(Base):
    __tablename__ = "ticket"
    tkt_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True
    )
    tkt_type: Mapped[types.ticket_type_t] = mapped_column(
        TicketType,
        nullable=False
    )
    tkt_usr: Mapped[tp.Optional[int]] = mapped_column(
        RefUsr
    )
    tkt_eaddr: Mapped[str] = mapped_column(
        ct.String,
        nullable=False
    )
    tkt_value: Mapped[str] = mapped_column(
        ct.String,
        nullable=False
    )
    tkt_deadline: Mapped[datetime.datetime] = mapped_column(
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
        # user is null => it is an account creation ticket
        implies(
            "tkt_usr is null",
            f"tkt_type = {types.TICKET_ACCOUNT_CREATION}"
        ),
    )


class CasAuth(Base):
    __tablename__ = "cas_auth"
    info = {
        "code": "cas_login",
        "doc": """This table controls CAS authentication. Each row
           gives access to one user."""
    }
    cas_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True,
        info={
            "ui_visible": True
        }
    )
    cas_enabled: Mapped[bool] = mapped_column(
        ct.Boolean,
        default=False,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": "1 if CAS authentication enabled for the user, 0 otherwise"
        }
    )
    cas_login: Mapped[str] = mapped_column(
        ct.String,
        nullable=False,
        unique=True,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": "login of the user on the CAS server"
        }
    )
    cas_usr: Mapped[int] = mapped_column(
        RefUsr,
        nullable=False,
        unique=True,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"""user which is granted access (references {\tt
               usr.usr\_code})"""
        }
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["cas_usr"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
    )


class LocalAuth(Base):
    __tablename__ = "local_auth"
    info = {
        "code": "loc_login",
        "doc": r"""This table controls local system
           authentication. Each row gives access to one user. The
           login used by the user to authenticate is her/his code. An
           empty password prevents the user from logging meaning that
           he/she has to first reset his/her password. If not empty,
           the password is given plain."""
    }
    loc_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True,
        info={
            "ui_visible": True
        }
    )
    loc_enabled: Mapped[bool] = mapped_column(
        ct.Boolean,
        nullable=False,
        default=False,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"""1 if local authentication is enabled for the
               user, 0 otherwise"""
        }
    )
    loc_login: Mapped[str] = mapped_column(
        ct.String,
        nullable=False,
        unique=True,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"login of the user"
        }
    )
    loc_password: Mapped[str] = mapped_column(
        ct.Password,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": "plain-text password (possibly empty)"
        }
    )
    loc_usr: Mapped[int] = mapped_column(
        RefUsr,
        nullable=False,
        unique=True,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"""user which is granted access (references {\tt
               usr.usr\_code})"""
        }
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["loc_usr"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
    )


class Tbl(Base):
    __tablename__ = "tbl"
    info = {
        "code": "tbl_name",
        "doc": """This table contains the list of names of tables
           which can be administrated through the web interface, i.e.,
           for which CSV file submission is allowed."""
    }
    tbl_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True,
        info={
            "ui_visible": True
        }
    )
    tbl_name: Mapped[str] = mapped_column(
        ct.String,
        nullable=False,
        unique=True,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"unique table name"
        }
    )


class Admin(Base):
    __tablename__ = "admin"
    info = {
        "doc": """This table defines grants administration privileges
           to users on tables."""
    }
    adm_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True,
        info={
            "ui_visible": True
        }
    )
    adm_usr: Mapped[int] = mapped_column(
        RefUsr,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"""user which is granted admin right (references
               {\tt usr.usr\_code})"""
        }
    )
    adm_tbl: Mapped[int] = mapped_column(
        RefTbl,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"""table on which this right admin right is
               granted (references {\tt tbl.tbl\_name})"""
        }
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


class Item(Base):
    __tablename__ = "item"
    itm_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True
    )
    itm_type: Mapped[types.item_type_t] = mapped_column(
        ItemType,
        nullable=False
    )
    itm_code: Mapped[tp.Optional[str]] = mapped_column(
        ct.ItemCode,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "check": "check_code"
        }
    )
    itm_title: Mapped[tp.Optional[str]] = mapped_column(
        ct.String,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "check": "check_title"
        }
    )
    itm_is_mcq: Mapped[bool] = mapped_column(
        ct.Boolean,
        nullable=False,
        default=False
    )
    itm_rnd: Mapped[bool] = mapped_column(
        ct.Boolean,
        nullable=False,
        default=True,
        info={
            "ui_visible": True,
            "ui_updatable": True
        }
    )
    itm_visible: Mapped[bool] = mapped_column(
        ct.Boolean,
        nullable=False,
        default=True,
        info={
            "ui_visible": True,
            "ui_updatable": True
        }
    )
    itm_date: Mapped[datetime.datetime] = mapped_column(
        ct.DateTime,
        nullable=False,
        server_default=now
    )
    itm_usr: Mapped[int] = mapped_column(
        RefUsr,
        nullable=False
    )
    itm_pack_spec: Mapped[tp.Optional[str]] = mapped_column(
        ct.PackSpec
    )
    itm_qst_type: Mapped[types.question_type_t] = mapped_column(
        QstType,
        default=types.QUESTION_TYPE_SINGLE,
        nullable=False
    )
    itm_qst_standalone: Mapped[bool] = mapped_column(
        ct.Boolean,
        default=False,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True
        }
    )
    itm_cho_correct: Mapped[bool] = mapped_column(
        ct.Boolean,
        nullable=False,
        default=False
    )
    itm_cho_last: Mapped[bool] = mapped_column(
        ct.Boolean,
        nullable=False,
        default=False
    )
    itm_mcq_mode: Mapped[types.mcq_mode_t] = mapped_column(
        McqMode,
        nullable=False,
        default=types.MCQ_MODE_EXAM,
        info={
            "ui_visible": True,
            "ui_updatable": True
        }
    )
    __table_args__ = (
        CheckConstraint(
            ItemType.get_constraint("itm_type")
        ),
        CheckConstraint(
            QstType.get_constraint("itm_qst_type")
        ),
        # it is a pack => pack spec is not null
        implies(
            f"itm_type = {types.ITEM_TYPE_PACK}",
            "itm_pack_spec is not null"
        ),
        # it is an mcq => it is a pack or an exercise
        implies(
            "itm_is_mcq",
            f"(itm_type = {types.ITEM_TYPE_EXERCISE} "
            f"or itm_type = {types.ITEM_TYPE_PACK})"
        ),
        # no code => it is a choice
        implies(
            "itm_code is null",
            f"itm_type = {types.ITEM_TYPE_CHOICE}"
        ),
        ForeignKeyConstraint(
            ["itm_usr"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
        UniqueConstraint(
            "itm_code",
            "itm_usr"
        )
    )
    def check_code(self) -> None:
        if not (
            self.itm_code is not None
            or self.itm_type == types.ITEM_TYPE_CHOICE
        ):
            raise errors.DBInvalidNullValue(
                "item",
                Item.itm_code.name
            )
    def check_title(self) -> None:
        if not (
            self.itm_title is not None
            or self.itm_type not in {
                types.ITEM_TYPE_EXERCISE, types.ITEM_TYPE_PACK
            }
        ):
            raise errors.DBInvalidNullValue(
                "item",
                Item.itm_title.name
            )
    def fmt(self) -> str:
        if self.itm_title is not None:
            result = f"{self.itm_title} [{self.itm_code}]"
        else:
            result = str(self.itm_code)
        return result


class ItemRelation(Base):
    __tablename__ = "item_relation"
    itr_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True
    )
    itr_parent: Mapped[int] = mapped_column(
        RefItem,
        nullable=False
    )
    itr_child: Mapped[int] = mapped_column(
        RefItem,
        nullable=False
    )
    itr_order: Mapped[int] = mapped_column(
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
        UniqueConstraint(
            "itr_parent",
            "itr_child"
        )
    )



class ItemInstance(Base):
    __tablename__ = "item_instance"
    iti_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True
    )
    iti_item: Mapped[int] = mapped_column(
        RefItem,
        nullable=False
    )
    iti_num: Mapped[int] = mapped_column(
        ct.Integer,
        nullable=False
    )
    iti_img: Mapped[tp.Optional[bytes]] = mapped_column(
        sa.LargeBinary
    )
    iti_uuid: Mapped[str] = mapped_column(
        ct.Uuid,
        nullable=False
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


class Tag(Base):
    __tablename__ = "tag"
    info = {
        "code": "tag_name",
        "doc": """This table defines tags that can be associated to MCQ
           items (e.g., questions)."""
    }
    tag_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True,
        info={
            "ui_visible": True
        }
    )
    tag_name: Mapped[str] = mapped_column(
        ct.String,
        nullable=False,
        unique=True,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": "unique tag name"
        }
    )
    tag_desc: Mapped[tp.Optional[str]] = mapped_column(
        ct.String,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": "tag description (possibly empty)"
        }
    )
    tag_color: Mapped[tp.Optional[str]] = mapped_column(
        ct.Color,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"tag color of the form \verb+#RRGGBB+ (possibly empty)"
        }
    )


class ItemTag(Base):
    __tablename__ = "item_tag"
    itg_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True
    )
    itg_item: Mapped[int] = mapped_column(
        RefItem,
        nullable=False
    )
    itg_tag: Mapped[int] = mapped_column(
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
    reg_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True
    )
    reg_usr: Mapped[int] = mapped_column(
        RefUsr,
        nullable=False
    )
    reg_exam: Mapped[int] = mapped_column(
        RefExam,
        nullable=False
    )
    reg_date: Mapped[datetime.datetime] = mapped_column(
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
    sub_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True
    )
    sub_type: Mapped[int] = mapped_column(
        SubmissionType,
        nullable=False
    )
    sub_date: Mapped[datetime.datetime] = mapped_column(
        ct.DateTime,
        nullable=False
    )
    sub_content: Mapped[str] = mapped_column(
        ct.String
    )
    sub_date_update: Mapped[datetime.datetime] = mapped_column(
        ct.DateTime
    )
    sub_exm_registration: Mapped[tp.Optional[int]] = mapped_column(
        RefRegistration
    )
    sub_visible: Mapped[bool] = mapped_column(
        ct.Boolean,
        default=False
    )
    sub_rev_usr: Mapped[tp.Optional[int]] = mapped_column(
        RefUsr
    )
    sub_rev_mcq: Mapped[tp.Optional[int]] = mapped_column(
        RefItem
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["sub_exm_registration"],
            ["registration.reg_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["sub_rev_usr"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["sub_rev_mcq"],
            ["item.itm_id"],
            ondelete="CASCADE"
        ),
        implies(
            f"sub_type = {types.SUBMISSION_TYPE_EXAM}",
            "sub_exm_registration is not null"
        ),
        implies(
            f"sub_type = {types.SUBMISSION_TYPE_REVIEW}",
            "sub_rev_usr is not null and sub_rev_mcq is not null"
        )
    )


class Answer(Base):
    __tablename__ = "answer"
    ans_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True
    )
    ans_submission: Mapped[int] = mapped_column(
        RefSubmission,
        nullable=False
    )
    ans_instance: Mapped[int] = mapped_column(
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
    info = {
        "code": "grp_name",
        "doc": "This table defines user groups."
    }
    grp_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True,
        info={
            "ui_visible": True
        }
    )
    grp_name: Mapped[str] = mapped_column(
        ct.String,
        nullable=False,
        unique=True,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": "unique group name"
        }
    )
    grp_parent: Mapped[tp.Optional[int]] = mapped_column(
        RefGrp,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"""parent group name (possibly empty, references
               {\tt grp.grp\_name})"""
        }
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


class Exam(Base):
    __tablename__ = "exam"
    exm_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True
    )
    exm_title: Mapped[str] = mapped_column(
        ct.String,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True
        }
    )
    exm_mcq: Mapped[int] = mapped_column(
        RefItem,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True
        }
    )
    exm_start: Mapped[datetime.datetime] = mapped_column(
        ct.DateTime,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True
        }
    )
    exm_duration: Mapped[int] = mapped_column(
        ct.PositiveInteger,
        nullable=False,
        default=60,
        info={
            "ui_visible": True,
            "ui_updatable": True
        }
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ["exm_mcq"],
            ["item.itm_id"],
            ondelete="CASCADE"
        ),
        CheckConstraint(
            "exm_duration > 0"
        ),
    )
    def end_time(self) -> datetime.datetime:
        return self.exm_start + datetime.timedelta(minutes=self.exm_duration)


class UsrGrp(Base):
    __tablename__ = "usr_grp"
    info = {
        "doc": "This table defines group memberships."
    }
    ugp_id = sa.Column(
        ct.Integer,
        primary_key=True,
        info={
            "ui_visible": True
        }
    )
    ugp_usr: Mapped[int] = mapped_column(
        RefUsr,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"user (references {\tt usr.usr\_code})"
        }
    )
    ugp_grp: Mapped[int] = mapped_column(
        RefGrp,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": r"group (references {\tt grp.grp\_name})"
        }
    )
    ugp_right: Mapped[types.usr_right_t] = mapped_column(
        UsrRight,
        nullable=False,
        info={
            "ui_visible": True,
            "ui_updatable": True,
            "doc": fr"""right given to the user on the group:
               {types.USR_RIGHT_VIEW} for view (right to view MCQ
               submitted for that group), {types.USR_RIGHT_SUBMIT} for
               submit (right to submit MCQ for that group)"""
        }
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


class McqGrp(Base):
    __tablename__ = "mcq_grp"
    mgp_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True
    )
    mgp_mcq: Mapped[int] = mapped_column(
        RefItem,
        nullable=False
    )
    mgp_grp: Mapped[int] = mapped_column(
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
            ["item.itm_id"],
            ondelete="CASCADE"
        ),
    )


class Project(Base):
    __tablename__ = "project"
    info = {
        "code": "prj_code"
    }
    prj_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True
    )
    prj_code: Mapped[str] = mapped_column(
        ct.ProjectCode,
        nullable=False
    )
    prj_usr: Mapped[int] = mapped_column(
        RefUsr,
        nullable=False
    )
    prj_title: Mapped[tp.Optional[str]] = mapped_column(
        ct.String,
        info={
            "ui_visible": True,
            "ui_updatable": True
        }
    )
    prj_uuid: Mapped[str] = mapped_column(
        ct.Uuid,
        nullable=False,
        unique=True
    )
    prj_copies: Mapped[int] = mapped_column(
        ct.Integer,
        nullable=False,
        default=10,
        info={
            "ui_visible": True,
            "ui_updatable": True
        }
    )
    prj_threshold: Mapped[float] = mapped_column(
        ct.Ratio,
        nullable=False,
        default=0.5,
        info={
            "ui_visible": True,
            "ui_updatable": True
        }
    )
    prj_amc_code: Mapped[str] = mapped_column(
        ct.String,
        nullable=False,
        default="code",
        info={
            "ui_visible": True,
            "ui_updatable": True
        }
    )
    prj_auto_assoc_attr: Mapped[tp.Optional[int]] = mapped_column(
        RefAttr,
        info={
            "ui_visible": True,
            "ui_updatable": True
        }
    )
    prj_src_type: Mapped[str] = mapped_column(
        ct.String,
        nullable=False,
        default="tex"
    )
    prj_done: Mapped[str] = mapped_column(
        ct.String,
        nullable=False
    )
    prj_history: Mapped[str] = mapped_column(
        ct.String,
        nullable=False
    )
    __table_args__ = (
        UniqueConstraint(
            "prj_usr",
            "prj_code"
        ),
        ForeignKeyConstraint(
            ["prj_usr"],
            ["usr.usr_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["prj_auto_assoc_attr"],
            ["attr.atr_id"],
            ondelete="CASCADE"
        ),
    )
    def title(self) -> str:
        return self.fmt()
    def fmt(self) -> str:
        if self.prj_title is not None:
            return self.prj_title.title()
        return str(self.prj_code)
    def dir_path(self) -> Path:
        return (
            Path(self.prj_uuid[0:2])
            / self.prj_uuid[2:4]
            / self.prj_uuid[4:]
        )


class PrjGrp(Base):
    __tablename__ = "prj_grp"
    pgp_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True
    )
    pgp_project: Mapped[int] = mapped_column(
        RefProject,
        nullable=False
    )
    pgp_grp: Mapped[int] = mapped_column(
        RefGrp,
        nullable=False
    )
    __table_args__ = (
        UniqueConstraint(
            "pgp_project",
            "pgp_grp"
        ),
        ForeignKeyConstraint(
            ["pgp_project"],
            ["project.prj_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["pgp_grp"],
            ["grp.grp_id"],
            ondelete="CASCADE"
        ),
    )


class Message(Base):
    __tablename__ = "message"
    msg_id: Mapped[int] = mapped_column(
        ct.Integer,
        primary_key=True
    )
    msg_type: Mapped[types.message_type_t] = mapped_column(
        MessageType,
        nullable=False
    )
    msg_title: Mapped[str] = mapped_column(
        ct.String,
        nullable=False
    )
    msg_date: Mapped[datetime.datetime] = mapped_column(
        ct.DateTime,
        nullable=False,
        server_default=now
    )
    msg_from: Mapped[int] = mapped_column(
        RefUsr,
        nullable=False
    )
    msg_to: Mapped[int] = mapped_column(
        RefUsr,
        nullable=False
    )
    msg_file_project: Mapped[tp.Optional[int]] = mapped_column(
        RefProject
    )
    msg_file_content: Mapped[tp.Optional[bytes]] = mapped_column(
        sa.LargeBinary
    )
    msg_file_name: Mapped[tp.Optional[str]] = mapped_column(
        ct.String
    )
    msg_sub: Mapped[tp.Optional[int]] = mapped_column(
        RefSubmission
    )
    __table_args__ = (
        UniqueConstraint(
            "msg_from",
            "msg_to",
            "msg_file_project"
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
        ForeignKeyConstraint(
            ["msg_sub"],
            ["submission.sub_id"],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ["msg_file_project"],
            ["project.prj_id"],
            ondelete="CASCADE"
        ),
        # message has type file => file content, code and name are not null
        implies(
            f"msg_type = {types.MESSAGE_TYPE_FILE}",
            "msg_file_content is not null "
            "and msg_file_project is not null "
            "and msg_file_name is not null"
        ),
        # message has type submission => submission is not null
        implies(
            f"msg_type = {types.MESSAGE_TYPE_SUBMISSION}",
            "msg_sub is not null"
        ),
    )


#####
# define attributes of foreign keys
#####

RefUsr.col = Usr.usr_id
RefUsr.fmt = lambda usr: usr.fmt()
RefProject.col = Project.prj_id
RefProject.fmt = lambda prj: str(prj.prj_code)
RefAttr.col = Attr.atr_id
RefAttr.fmt = lambda attr: str(attr.atr_code)
RefTbl.col = Tbl.tbl_id
RefTbl.fmt = lambda tbl: str(tbl.tbl_name)
RefSubmission.col = Submission.sub_id
RefSubmission.fmt = lambda sub: str(sub.sub_id)
RefGrp.col = Grp.grp_id
RefGrp.fmt = lambda grp: str(grp.grp_name)
RefTag.col = Tag.tag_id
RefTag.fmt = lambda tag: str(tag.tag_name)
RefExam.col = Exam.exm_id
RefExam.fmt = lambda exam: str(exam.exm_id)
RefRegistration.col = Registration.reg_id
RefRegistration.fmt = lambda reg: str(reg.reg_id)
RefItemInstance.col = ItemInstance.iti_id
RefItemInstance.fmt = lambda iti: str(iti.iti_id)
RefItem.col = Item.itm_id
RefItem.fmt = lambda item: item.fmt()


#####
# all listeners defined below
#####

def check_item_not_in_exam_submission(
        conn: Connection,
        itm_id: int
) -> None:

    # make sure that the item is not part of an exam submission
    query = select(
        Exam
    ).where(
        (ItemInstance.iti_item == itm_id)
        & (ItemInstance.iti_id == Answer.ans_instance)
        & (Answer.ans_submission == Submission.sub_id)
        & (Submission.sub_type == types.SUBMISSION_TYPE_EXAM)
        & (Submission.sub_exm_registration == Registration.reg_id)
        & (Registration.reg_exam == Exam.exm_id)
    )
    exam = conn.execute(query).first()
    if exam is not None:
        title = exam.exm_title
        raise errors.DBDeletionOfItemReferencedInExamSubmission(title)


def before_delete_item_relation(
        mapper: Mapper[tp.Any],
        conn: Connection,
        target: ItemRelation
) -> None:
    check_item_not_in_exam_submission(conn, target.itr_parent)


def before_delete_item(
            mapper: Mapper[tp.Any],
            conn: Connection,
            target: Item
    ) -> None:

    # when we delete a question we delete all choices in it
    check_item_not_in_exam_submission(conn, target.itm_id)
    if target.itm_type == types.ITEM_TYPE_QUESTION:
        query_delete = delete(
            Item
        ).where(
            (ItemRelation.itr_parent == target.itm_id)
            & (ItemRelation.itr_child == Item.itm_id)
        )
        conn.execute(query_delete)

        
def before_insert_exam(
        mapper: Mapper[tp.Any],
        conn: Connection,
        target: Exam
) -> None:

    # if the title of a new exam is None we set it to the QCM's title
    if target.exm_title in ("", None) and target.exm_mcq is not None:
        query = select(Item).where(Item.itm_id == target.exm_mcq)
        mcq = conn.execute(query).first()
        if mcq is not None:
            target.exm_title = mcq.itm_title


def after_insert_project(
        mapper: Mapper[tp.Any],
        conn: Connection,
        target: Project
) -> None:
    from webamc import project
    if not types.is_success(project.create_files(target)):
        raise errors.DBIOError()


def after_delete_project(
        mapper: Mapper[tp.Any],
        conn: Connection,
        target: Project
) -> None:
    from webamc import project
    if not types.is_success(project.delete_files(target)):
        raise errors.DBIOError()


def before_insert_item_relation(
        mapper: Mapper[tp.Any],
        conn: Connection,
        target: ItemRelation
) -> None:
    # when we insert in ItemRelation we make sure that we still have a
    # tree, this requires to perform a graph search
    todo = [target.itr_child, target.itr_parent]
    done: set[int] = set(todo)
    while todo != list():
        item = todo[0]
        todo = todo[1:]
        query = select(
            ItemRelation.itr_parent
        ).where(
            ItemRelation.itr_child == item
        )
        for parent in conn.scalars(query):
            if parent in done:
                query_parent = select(Item).where(Item.itm_id == parent)
                item_parent = conn.execute(query_parent).first()
                assert item_parent is not None
                assert item_parent.itm_code is not None
                raise errors.DBItemRelationInvalid(item_parent.itm_code)
            todo.append(parent)
            done.add(parent)


def before_delete_exam(
        mapper: Mapper[tp.Any],
        conn: Connection,
        target: Exam
) -> None:
    query = select(
        Submission
    ).where(
        (Registration.reg_exam == target.exm_id)
        & (Submission.sub_exm_registration == Registration.reg_id)
    )
    if conn.execute(query).first() is not None:
        raise errors.DBDeletionOfExamWithSubmissions(target.exm_title)


# checks performed during or insert or update
def basic_checks(
        tbl: sa.sql.schema.Table,
        conn: Connection,
        target: tp.Any,
        row_id: None | int
) -> None:

    # replace "" values by None and None by a default value
    for col in tbl.columns:
        cname = col.name
        if hasattr(target, cname) and getattr(target, cname) == "":
            setattr(target, cname, None)
        if isinstance(col.type, ct.ColType) and getattr(target, cname) is None:
            setattr(target, cname, col.type.default())

    tname = tbl.name
    pkey = next(c for c in tbl.columns if c.primary_key)
    for col in tbl.columns:
        if "check" in col.info:
            getattr(target, col.info["check"])()

        cname = col.name
        val = getattr(target, cname, None)
        null_val = val is None

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


listener_t = tp.Callable[[Mapper[tp.Any], Connection, tp.Any], None]
def before_insert(t: tp.Type[Base]) -> listener_t:
    def result(
            mapper: Mapper[tp.Any],
            conn: Connection,
            target: tp.Any
    ) -> None:
        tbl: sa.sql.schema.Table = t.__table__  # type: ignore
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
                    and col.default is None
                    and col.server_default is None
            ):
                raise errors.DBInvalidNullValue(tname, cname)
    return result


def before_update(t: tp.Type[Base]) -> listener_t:
    def result(
            mapper: Mapper[tp.Any],
            conn: Connection,
            target: tp.Any
    ) -> None:
        tbl: sa.sql.schema.Table = t.__table__  # type: ignore
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
sa.event.listen(Exam, "before_insert", before_insert_exam)
sa.event.listen(Exam, "before_delete", before_delete_exam)
sa.event.listen(Item, "before_delete", before_delete_item)
sa.event.listen(ItemRelation, "before_delete", before_delete_item_relation)
sa.event.listen(ItemRelation, "before_insert", before_insert_item_relation)
sa.event.listen(Project, "after_insert", after_insert_project)
sa.event.listen(Project, "after_delete", after_delete_project)
for t in Base.__subclasses__():
    sa.event.listen(t, "before_insert", before_insert(t))
    sa.event.listen(t, "before_update", before_update(t))
