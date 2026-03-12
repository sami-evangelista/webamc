#!/usr/bin/env python3

from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.session import Session

from webamc.all import *
from webamc.util import fmt, security
from . import ui


class ColType:
    input_type: tp.Type[ui.Input]
    doc_color = "black"
    @classmethod
    def val_chk(cls, val: tp.Any, **kwargs: tp.Any) -> types.db_base_val_t:
        raise ValueError
    @classmethod
    def val_fmt(cls, val: types.db_base_val_t, **kwargs: tp.Any) -> str:
        if val is None:
            return "NA"
        if isinstance(val, str) and str(val) == "":
            return "-"
        return str(val)
    @classmethod
    def val_transform(cls, val: types.db_base_val_t) -> types.db_base_val_t:
        return val
    @classmethod
    def get_input(cls, col: sa.Column[tp.Any], **kwargs: tp.Any) -> ui.Input:
        return cls.input_type(col)


class Date(sa.Date, ColType):
    input_type = ui.Date
    doc_color = "violet"
    @classmethod
    def val_chk(cls, val: tp.Any, **kwargs: tp.Any) -> types.db_base_val_t:
        return datetime.date.fromisoformat(val)
    @classmethod
    def val_fmt(cls, val: types.db_base_val_t, **kwargs: tp.Any) -> str:
        if val is None:
            return "NA"
        if not isinstance(val, datetime.date):
            raise ValueError
        return fmt.fmt_date(val)


class DateTime(sa.DateTime, ColType):
    input_type = ui.DateTime
    doc_color = "purple"
    @classmethod
    def val_chk(cls, val: tp.Any, **kwargs: tp.Any) -> types.db_base_val_t:
        return datetime.datetime.fromisoformat(val)
    @classmethod
    def val_fmt(cls, val: types.db_base_val_t, **kwargs: tp.Any) -> str:
        if val is None:
            return "NA"
        if not isinstance(val, datetime.datetime):
            raise ValueError
        return fmt.fmt_datetime(val)


class String(sa.String, ColType):
    input_type: tp.Type[ui.Input] = ui.Text
    doc_color = "blue"
    @classmethod
    def val_chk(cls, val: tp.Any, **kwargs: tp.Any) -> types.db_base_val_t:
        return str(val)


class Boolean(sa.Boolean, ColType):
    input_type = ui.Checkbox
    doc_color = "yellow"
    @classmethod
    def val_chk(cls, val: tp.Any, **kwargs: tp.Any) -> types.db_base_val_t:
        return bool(val)


class Integer(sa.Integer, ColType):
    input_type = ui.Number
    doc_color = "red"
    @classmethod
    def val_chk(cls, val: tp.Any, **kwargs: tp.Any) -> types.db_base_val_t:
        return int(val)


class ConstrainedString(String):
    regexp: None | str = None
    len_range: tuple[None | int, None | int] = (None, None)
    @classmethod
    def val_chk(cls, val: tp.Any, **kwargs: tp.Any) -> types.db_base_val_t:
        result = str(val)
        if cls.regexp is not None and not re.match(cls.regexp, result):
            raise ValueError
        if cls.len_range[0] is not None and len(result) < cls.len_range[0]:
            raise ValueError
        if cls.len_range[1] is not None and len(result) > cls.len_range[1]:
            raise ValueError
        return result


class Color(ConstrainedString):
    input_type = ui.Color
    regexp = "#[0-9a-fA-F]{6}"


class Eaddr(ConstrainedString):
    regexp = r"^\S+@\S+\.\S+$"


class LargeString(String):
    input_type = ui.Textarea


class Name(String):
    @classmethod
    def val_fmt(cls, val: types.db_base_val_t, **kwargs: tp.Any) -> str:
        if val is None:
            return "-"
        return str(val).upper()


class FstName(String):
    @classmethod
    def val_fmt(cls, val: types.db_base_val_t, **kwargs: tp.Any) -> str:
        if val is None:
            return "-"
        return str(val).title()


class Password(ConstrainedString):
    input_type = ui.Password
    len_range = (8, None)
    @classmethod
    def val_transform(cls, val: types.db_base_val_t) -> types.db_base_val_t:
        if val is None:
            return None
        return security.hash_password(str(val))


class IntEnum(Integer):
    values: dict[int, str]
    @classmethod
    def get_constraint(cls, name: str) -> str:
        values = ", ".join(str(val) for val in cls.values.keys())
        return f"{name} in ({values})"
    @classmethod
    def val_chk(cls, val: tp.Any, **kwargs: tp.Any) -> int:
        result = int(val)
        if result not in cls.values:
            raise ValueError
        return result
    @classmethod
    def val_fmt(cls, val: types.db_base_val_t, **kwargs: tp.Any) -> str:
        if val is None:
            return "NA"
        return str(cls.values[cls.val_chk(val, **kwargs)])
    @classmethod
    def get_values(cls, **kwargs: tp.Any) -> dict[int, str]:
        return cls.values
    @classmethod
    def get_input(cls, col: sa.Column[tp.Any], **kwargs: tp.Any) -> ui.Input:
        return ui.Select(col, cls.get_values(**kwargs))


class ForeignKey(IntEnum):
    col: InstrumentedAttribute[int]
    fmt: tp.Callable[[sa.Row[tp.Any]], str]
    @classmethod
    def val_chk(cls, val: tp.Any, **kwargs: tp.Any) -> int:
        result = int(val)
        dbs = tp.cast(Session, kwargs["dbs"])
        tbl = cls.col.table
        row = dbs.query(tbl).where(cls.col == result).first()
        if row is None:
            raise ValueError
        return result
    @classmethod
    def val_fmt(cls, val: types.db_base_val_t, **kwargs: tp.Any) -> str:
        if val is None:
            return "NA"
        dbs = tp.cast(Session, kwargs["dbs"])
        tbl = cls.col.table
        row = dbs.query(tbl).where(cls.col == val).first()
        return cls.fmt(row)
    @classmethod
    def get_values(cls, **kwargs: tp.Any) -> dict[int, str]:
        dbs = tp.cast(Session, kwargs["dbs"])
        tbl = cls.col.table
        query = dbs.query(cls.col, tbl)
        return {
            getattr(row, cls.col.name): cls.fmt(row)
            for row in query.all()
        }
